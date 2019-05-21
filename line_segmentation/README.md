# Automatic Line Segmentation

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
 python  main.py  /path/to/shapefiles/  /path/to/config/file
```
For example:  `python main.py maps config.json`


When done, we can export the data from the `PostgreSQL` DB tablesinto `csv` table files.
In the `PostgreSQL` shell, run each command of the following:
```
COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM contain) t) TO '/tmp/contain.csv';
COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM geom) t) TO '/tmp/geom.csv';
COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM sameas) t) TO '/tmp/sameas.csv';
COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM map) t) TO '/tmp/map.csv';
```