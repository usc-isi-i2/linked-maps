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
python main.py -d /path/to/shapefiles/ -c /path/to/config/file -r
```
For example:  `python main.py -d maps_partial -c config.json -r -v`


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

    -->