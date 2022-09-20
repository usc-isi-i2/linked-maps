# Linked Maps

A framework for automatic conversion of vector data - extracted from USGS historical topographic map archives - into linked and publishable spatio-temporal data as `RDF`. The resulting knowledge graphs can be easily queried and visualized to understand the changes of features in specific regions over time.

The process runs in three steps which can be executed separately (see the following sections):
1. __Automatic geometric feature partitioning__
2. __Geo entity-linking__
3. __Modeling the data into `RDF` (constructing the knowledge graph)__

Additionally, we provide a `dockerfile` and instructions on how to run the full pipeline automatically using [Docker](https://www.docker.com/), and provide a front-end `flask` application to allow running queries - over a defined `SPARQL` endpoint - and visualizing their results.

This is the implementation accompanying the paper _Building Linked Spatio-Temporal Data from Vectorized Historical Maps_ published in the 17th Extended Semantic Web Conference (ESWC 2020).

------------------

### Preparing to run the program

The environment framework we use is [`anaconda`](https://www.anaconda.com/distribution/), then you should do the following:

1. Create a new environment from scratch with the `python3.7`:
   ```
   conda create -n linkedmaps python=3.7
   ```
2. Activate the environment:
   ```
   conda activate linkedmaps
   ```
3. Install [GDAL](https://gdal.org/):
   ```
   conda install -c conda-forge gdal
   ```
4. Install [`PostgreSQL`](https://www.postgresql.org/) with [`PostGIS`](https://postgis.net/) and then:<br />
    4.1. Create the database in which the segmentation operations will run<br />
    4.2. Create the `PostGIS` extension on that database: `CREATE EXTENSION postgis;`
5. Install the `requirements.txt` file using `pip`:
   ```
   pip install -r requirements.txt
   ```

------------------

## Automatic geometric feature partitioning

The first task in our pipeline is the creation of geometric building-blocks that can represent the various geographic features (e.g., railway, wetland) across different map editions of the same region. We use `PostgreSQL` (with `PostGIS` extension and integration using `python`) to accomplish this task. The following script takes a directory holding a collection of vector data as `shapefile`s and a simple configuration file as input, and produces a collection of `jl` (JSON Lines) files capturing the data and metadata of the partitioned segments.

First, make sure that:
* Your configuration file (`config.json`) is correct (set the database access attributes accordingly, and the geometry type: `MULTILINESTRING` or `MULTIPOLYGON`).
* The name of each `shapefile` in your "maps" directory matches the temporal extent of the map edition it represents (the year it was published).

How to run:
```
python main.py -d <path_to_shapefiles>
               -c <path_to_config_file>
               -r
               -o <path_to_output_file>
```
For example:
```
python main.py -d data/railroads/ca/ -c config.json -r -o /tmp/line_seg.jl
```
will produce the files: `/tmp/line_seg.geom.jl` (geometry), `/tmp/line_seg.seg.jl` (segments) and `/tmp/line_seg.rel.jl` (relations).


## Geo entity-linking

In this task we link the extracted building-blocks from the processed historical maps to additional knowledge bases on the web (a task of geo entity-linking/matching). We utilize a reverse-geocoding service  to map the resulting segments to instances on `OpenStreetMap`. The following script takes a "geometry" `jl` file as input, and produces an additional `jl` file holding the `URI`s of the distant instances we captured.

How to run:
```
python linked_maps_to_osm.py -g <path_to_geometry_file>
                             -f <desired_feature>
```
For example:
```
python linked_maps_to_osm.py -g /tmp/line_seg.geom.jl -f railway
```
will produce the file `/tmp/line_seg.geom.osm.jl`


## Modeling the data into `RDF`

Now we need to construct the final knowledge graph by generating `RDF` triples following a predefined semantic model that builds on `GeoSPARQL` and using the data we generated in the previous steps. We utilize the `RDFLib` library to accomplish this task. The following script takes all the `jl` files we generated earlier as input and produces a `ttl` file encoding our final `RDF` data.


How to run:
```
python generate_graph.py -g <path_to_geometry_file>
                         -s <path_to_segments_file>
                         -r <path_to_relations_file>
                         -l <path_to_osm_uris_file>
                         -o <path_to_output_file>
```
For example:
```
python generate_graph.py -g /tmp/line_seg.geom.jl -s /tmp/line_seg.seg.jl -r /tmp/line_seg.rel.jl -l /tmp/line_seg.geom.osm.jl -o /tmp/linked_maps.maps.ttl
```
will produce the file `/tmp/linked_maps.maps.ttl`

------------------

## Run the whole pipeline using Docker

Docker allows an isolated OS-level virtualization and thus a completely separate environment in which you can run the whole process without performing any additional installations on your machine.

### Option 1
Building the image manually:
```
docker build -t shbita/uscisi_linkedmaps .
```

### Option 2
Pull the image from Docker-Hub:
```
docker pull shbita/uscisi_linkedmaps
```

### Running the container
Prior to running the Docker container, the map `shapefiles` (`*.shp, *.shx`) should be inserted in a local directory (host) that should be virtually mapped to `/linked-maps/maps` on the container. The output files and the generated `ttl` file will be dumped to the same directory. As in:
```
docker run -v <hostmachine_volume>:/linked-maps/maps shbita/uscisi_linkedmaps:latest
```
For example:
```
docker run -v /tmp/maps:/linked-maps/maps -it shbita/uscisi_linkedmaps:latest
```
Make sure that:
1. The volume you are using (on your local machine) has 'File Sharing' enabled in the Docker settings
2. You are using full paths (on both the local machine and the docker container)
3. The user running the docker command has access privlege (can be done by `sudo chmod 777 <hostmachine_volume>`)

------------------

## Querying and visualizing your data

Our front-end allows querying and visualizing your linked-maps-style `RDF` data.
We use the `flask` module for the front-end and utilize Google-Maps' API to visualize the geo-data over earth's map. We assume that you are already running a `SPARQL` endpoint.

_If you do not have a running `SPARQL` endpoint, we suggest using `apache-jena-fuseki`, it is a relatively lightweight triplestore, easy to use, and provides a programmatic environment. Once ready, you can run the following command to initiate the triplestore (and the `SPARQL` endpoint) from `fuseki`'s root directory_:
```
./fuseki-server --file <your_ttl_file> </ServiceName>
```
_For example_:
```
./fuseki-server --file /linked-maps/data/railroads/ca/linked_maps.railroads.ca.ttl /linkedmaps
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

### Data

Our data is licensed under [CC0](https://creativecommons.org/publicdomain/zero/1.0/legalcode).
The data files are organized as follows:
```
.
└── data
    ├── railroads
    │  ├── ca
    │  │   ├── [1950c|1954c|1958c|1962c|1984c|1988c|2001c].shp/shx/prj/qpj/dbf # shapefiles describing railroad networks from different points in time pertaining to a region in Bray, California
    │  │   └── linked_maps.railroads.ca.ttl # RDF data for railroad networks in Bray, California
    │  └── co
    │      ├── [1942|1950|1957|1965].shp/shx/prj/qpj/dbf # shapefiles describing railroad networks from different points in time pertaining to a region in Louisville, Colorado
    │      └── linked_maps.railroads.co.ttl # RDF data for railroad networks in Louisville, Colorado
    └── wetlands
       ├── ca
       │   ├── [1961|1990|1993|2018].shp/shx/prj/qpj/dbf # shapefiles describing wetland areas from different points in time pertaining to a region in Bieber, California
       │   └── linked_maps.wetlands.ca.ttl # RDF data for wetland areas in Bieber, California
       ├── fl
       │   ├── [1956|1987|2020].shp/shx/prj/qpj/dbf # shapefiles describing wetland areas from different points in time pertaining to a region in Palm Beach, Florida
       │   └── linked_maps.wetlands.fl.ttl # RDF data for wetland areas in Palm Beach, Florida
       └── tx
           ├── [1959|1995|2020].shp/shx/prj/qpj/dbf # shapefiles describing wetland areas from different points in time pertaining to a region in Duncanville, Texas
           └── linked_maps.wetlands.tx.ttl # RDF data for wetland areas in Duncanville, Texas
```

The resulting knowledge graph (all `ttl` files combined) is published and available as linked data [here](https://linked-maps.isi.edu/) (with compliant IRI dereferenciation), along with a designated SPARQL endpoint [here](https://linked-maps.isi.edu/sparql).

------------------

### Citing

If you would like to cite this work in a paper or a presentation, the following is recommended (`BibTeX` entry):
```
@article{shbitabuilding,
  title={Building spatio-temporal knowledge graphs from vectorized topographic historical maps},
  author={Shbita, Basel and Knoblock, Craig A and Duan, Weiwei and Chiang, Yao-Yi and Uhl, Johannes H and Leyk, Stefan},
  journal={Semantic Web},
  number={Preprint},
  pages={1--23},
  publisher={IOS Press}
}
```
