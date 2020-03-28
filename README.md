# Linked Maps

A framework for unsupervised conversion of vector data - extracted from USGS historical topographic map archives - into linked and publishable spatio-temporal data as `RDF`. The resulting graphs can be easily queried and visualized to understand the changes in specific regions over time.

The process is separated into three steps which can be executed separately (see the following sections):
1. __Automatic Feature Segmentation__
2. __Geo-linking__
3. __Modeling the data into RDF__

Additionally, we provide a `dockerfile` and instructions on how to run the full pipeline automatically using Docker, and provide a front-end `flask` application to allow running queries - over some `SPARQL` endpoint - and visualizing their results.

This is the implementation accompanying the paper _Building Linked Spatio-Temporal Data from Vectorized Historical Maps_ to be published on the 17th Extended Semantic Web Conference (ESWC 2020).

------------------

### Preparing to run the program

The environment framework I used was [`anaconda`](https://www.anaconda.com/distribution/), then I did the following:

1. Create a new environment from scratch with the `python` 3.6:
   ```
   conda create -n linkedmaps python=3.6
   ```
2. Activate the environment:
   ```
   conda activate linkedmaps
   ```
3. Install [GDAL](https://gdal.org/):
   ```
   conda install -c conda-forge gdal
   ```
4. Install [`PostgreSQL`](https://www.postgresql.org/) with [`PostGIS`](https://postgis.net/) and then
    4.1. Create the database in which the line segmentation program will perform
    4.2 Create the `PostGIS` extension on that database: `CREATE EXTENSION postgis;`
5. Install the `requirements.txt` file using `pip`:
   ```
   pip install -r requirements.txt
   ```

------------------

## Automatic Feature Segmentation

The first task in our pipeline is the creation of segment partitions (elements) that can represent the various geographic features (e.g., railroad network) across different map editions of the same region. We use `PostgreSQL` (with `PostGIS` extension and integration using `python`) to accomplish this task. The following script takes a directory holding a collection of `shapefile`s and a simple configuration file as input, and produces a collection of `jl` (JSON Lines) files capturing the data and metadata of the partitioned segments.

First, make sure that your configuration file (`config.json`) is correct (set the database access attributes accordingly).

How to run:
```
python main.py -d <path_to_shapefiles>
               -c <path_to_config_file>
               -r
               -o <path_to_output_file>
```
For example:
```
python main.py -d maps_bray -c config.json -r -o /tmp/line_seg.jl
```
will produce the files: `/tmp/line_seg.geom.jl` (geometry), `/tmp/line_seg.seg.jl` (segments), `/tmp/line_seg.rel.jl` (relations).


## Geo-linking

In this task we link the extracted segments from the processed historical maps to additional knowledge bases on the web (a task of geo-entity matching). We utilize a reverse-geocoding service (`OpenStreetMap`) to map the resulting segments to instances on the semantic web (`LinkedGeoData`). "geometry" `jl` file as input, and produces an additional `jl` file holding the `URI`s of the distant instances we captured.

How to run:
```
python linked_maps_to_osm.py -g <path_to_geometry_file>
                             -f <desired_feature>
```
For example:
```
python linked_maps_to_osm.py -g /tmp/line_seg.geom.jl -f railway
```
will produce the file `/tmp/line_seg.geom.lgd.jl`


## Modeling the data into RDF

Now we need to construct the final knowledge graph by generating `RDF` triples following a predefined semantic model that builds on GeoSPARQL and using the data we generated in the previous steps. We utilize the `RDFLib` library to accomplish this task. The following script takes all the `jl` files we generated earlier as input and produces a `ttl` file encoding our final `RDF` data.


How to run:
```
python generate_graph.py -g <path_to_geometry_file>
                         -s <path_to_segments_file>
                         -r <path_to_relations_file>
                         -l <path_to_linkedgeodata_uris_file>
                         -o <path_to_output_file>
```
For example:
```
python generate_graph.py -g /tmp/line_seg.geom.jl -s /tmp/line_seg.seg.jl -r /tmp/line_seg.rel.jl -l /tmp/line_seg.geom.lgd.jl -o /tmp/maps_bray.linked_maps.ttl
```
will produce the file `/tmp/maps_bray.linked_maps.ttl`

------------------

## Docker

_TODO_

<!--

Prior to building the image (and running the container), map shapefiles (`*.shp, *.shx`) should be inserted in `maps` directory.

Build image:
```
docker build -t linked-maps .
```

The generated ttl file will be dumped to `results` directory on the container upon finishing. It is recommended to set a shared volume between the host and the container in order to obtain access to the output files:
```
docker run -v /volume/on/your/host/machine:/volume/on/container linked-maps:latest
```
For example: `docker run -v /home/shbita/linked-maps/res:/linked-maps/results -it linked-maps:latest`
Make sure that:
1. The volume you're using (on your local machine) has 'File Sharing' enabled in the Docker settings.
2. You're using full paths (on both local machine and docker container)
3. The user running the docker command has access privlege (can be done by `sudo chmod 777 /volume/on/your/host/machine`)

-->

------------------

## Querying and visualizing your data

Our front-end allows querying and visualizing your linked-maps-style RDF data.
We use the `flask` module for the front-end and utilize Google-Maps' API to visualize the geo-data over earth's map. We assume that you are already running a SPARQL endpoint.

_If you do not have a running SPARQL endpoint, we suggest using `apache-jena-fuseki`, it is a relatively lightweight triplestore, easy to use, and provides a programmatic environment. Once ready, you can run the following command to initiate the triplestore (and the SPARQL endpoint) from `fuseki`'s root directory_:
```
./fuseki-server --file <your_ttl_file> </ServiceName>
```
_For example_:
```
./fuseki-server --file /linked-maps/bray_data/bray.linked_maps.ttl /linkedmaps
```

Now run the flask server:
```
python ui/main.py -s <sparql_endpoint_path>
```
For example:
```
python ui/main.py -s http://localhost:3030/linkedmaps/query
```
then navigate to `http://localhost:5000/`

------------------

### Citing

If you would like to cite the this work in a paper or presentation, the following is recommended (BibTeX entry):
```
@inproceedings{shbita2020building,
  title={Building Linked Spatio-Temporal Data from Vectorized Historical Maps},
  author={Shbita, Basel and Knoblock, Craig A and Duan, WeiWei and Chiang, Yao-Yi and Uhl, Johannes H and Leyk Stefan},
  booktitle={Extended Semantic Web Conference},
  pages={},
  year={2020},
  organization={Springer}
}
```