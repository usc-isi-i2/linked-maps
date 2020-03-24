# Linked Maps Project

A framework to convert vector data extracted from multiple historical maps into linked spatio-temporal data.
The resulting RDF graphs can be queried and visualized to understand the changes in specific regions through time.

The process is separated into three steps:

1. Automatic line segmentation using `PostgreSQL` (with `Postgis` extension and integration using `Python`). 
2. Modeling the data into RDF.
3. Running queries using `SPARQL` on Apache Jena. Follow the README in directory `query_and_viz/` (See README in directory `app/` for a mock-up of our front-end).

## Automatic Line Segmentation

To run this line segmentation program, we need to setup the environment.
1. Install Python 2.7 and do
```
pip install psycopg2 osgeo
```
2. Install PostgreSQL with PostGIS. This program was tested with PostgreSQL 9.6 and PostGIS 2.4
3. Create the database in which the line segmentation program will perform
4. Create the Postgis extension on that database
```
 CREATE EXTENSION postgis;
```
5. Edit your config.json accordingly.
6. Run this command
```
python main.py -d /path/to/shapefiles/ -c /path/to/config/file -r -o /path/to/output/file
```
For example:  `python main.py -d maps -c config.json -r -o /tmp/line_seg.jl`


## Modeling the data into RDF

Prior to this step, the user most create the data (3 `jl` files: geometry, segments, relations) from the previous step of line-segmentation.
The script `generate_graph.py` processes the files and generates an output file which contains the required RDF we should upload later to Apache Jena.

How to run:
```
python generate_graph.py -g /path/to/geometry/file -s /path/to/segments/file -r /path/to/relations/file
```
For example: `python generate_graph.py -g line_seg.geom.jl -s line_seg.seg.jl -r line_seg.rel.jl`

<!--

Finalize Visualization! Revise this:

`docker cp linkedmaps:/linked-maps/lnkd_mp_grph.ttl ./lnkd_mp_grph.ttl`
`docker build -t jena-fuseki ./query_and_viz/`
`docker run -p 3030:3030 -e ADMIN_PASSWORD=1234 jena-fuseki`

Open your browser and enter `http://localhost:3030/`
Manage datasets -> add new dataset -> create dataset
Select "upload data" on the dataset you created, and 
upload the `lnkd_mp_grph.ttl` found in the current working directory
Now you can run SPARQL queries under "dataset" section



## Docker

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

## Query and visualize you data
Our front-end allows querying and visualizing your linked-maps-style geo-triples data.
We use the `flask` module to create the UI and utilize Google-Maps' API to visualize the geo-data over earth's map. We assume that you are already running a SPARQL endpoint.

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
python ui/main.py
```
And navigate to `http://localhost:5000/`