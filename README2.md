# Linked Maps Project

A framework to convert vector data extracted from multiple historical maps into linked spatio-temporal data.
The resulting RDF graphs can be queried and visualized to understand the changes in specific regions through time.

The process is separated into three steps:

1. Automatic line segmentation.
2. Modeling the data into RDF.
3. Running queries using `SPARQL` on Apache Jena.

##Prerequisites 
1. git
2. docker

Go to bash and execute the following commands.
- `git clone https://github.com/usc-isi-i2/linked-maps.git`
- `cd linked-maps`
- `docker build -t linkedmaps:your_tag .`
- `docker run -it -d --name linkedmaps linkedmaps:your_tag /bin/bash`
- `docker exec -it linkedmaps /bin/bash`
    
This will take you inside the container as postgres user.
Now run the following commands from inside the container.

1. `/etc/init.d/postgresql start && createdb linkedmaps && psql linkedmaps -c "CREATE EXTENSION Postgis;"` 
2. `python3 main.py maps config.json `
3. `psql linkedmaps -c " COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM contain) t) TO '/tmp/contain.csv';COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM geom) t) TO '/tmp/geom.csv';COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM sameas) t) TO '/tmp/sameas.csv';COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM map) t) TO '/tmp/map.csv';"`
4. `exit` 

Once having exit the container. RUN the following commands from host bash

- `docker exec -it --user root linkedmaps /bin/bash "python3 construct_triples.py"`


