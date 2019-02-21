# Automated Line Segmentation

The abstract idea of line segmentation shall be described in section 2 of [this paper](http://usc-isi-i2.github.io/papers/lin18.pdf) for more info. 

To run this line segmentation program, we need to setup the environment.

1. Installed PostgreSQL with PostGIS. This program was tested with PostgreSQL 9.6 and PostGIS 2.4
2. Create the database in which the line segmentation program will perform
3. Create the Postgis extension on that database
```
 CREATE EXTENSION postgis;
 ```
 4. Edit your config.json accordingly.
 5. Run this command
 ```python main.py -a /path/to/shpfiles/ /path/to/config/file/```
This will run the line segmentation program in automatic mode, which will perform segmentation for all shapefiles in the folder. Alternatively, run 
```python main.py -m``` 
This will run the line segmentation program manually. You will need to specify what do you want do by yourselves.
