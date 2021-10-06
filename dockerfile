FROM ubuntu:16.04
MAINTAINER Basel Shbita "shbita@usc.edu"

# Set the working directory to /linked-maps
WORKDIR /linked-maps

# install python3.7 and wget
RUN apt-get update && \
    apt-get install -y software-properties-common wget && \
    add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt-get install -y build-essential python3.7-dev python3-pip git

# install GDAL/OGR
RUN add-apt-repository -y ppa:ubuntugis/ppa && \
    apt-get update -y && \
    apt-get install -y gdal-bin libgdal-dev python-gdal python3-gdal

# install postgresql and postgis
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main" > /etc/apt/sources.list.d/PostgreSQL.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y postgresql-11 postgresql-11-postgis-2.5 postgresql-11-postgis-2.5-scripts postgis

# update pip
RUN python3.7 -m pip install pip --upgrade

# set working directory to /linked-maps
COPY ./ /linked-maps
WORKDIR /linked-maps

# install additional requirements
RUN pip3.7 install -r requirements.txt

# create 'maps' dir and grant access to it for all users
RUN mkdir maps && chmod 777 maps

RUN mv /usr/lib/python3/dist-packages/osgeo/_gdal.cpython-35m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/osgeo/_gdal.so && \
    mv /usr/lib/python3/dist-packages/osgeo/_ogr.cpython-35m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/osgeo/_ogr.so && \
    mv /usr/lib/python3/dist-packages/osgeo/_osr.cpython-35m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/osgeo/_osr.so

# switch to user 'postgres'
USER postgres

# initiate postgresql service and create database with postgis extension
# then run the pipeline
CMD /etc/init.d/postgresql start && \
    createdb linkedmaps && \
    psql linkedmaps -c "CREATE EXTENSION postgis;" && \
    python3.7 main.py -d maps -c config.json -r -o maps/line_seg.jl 2>&1 | tee maps/line_seg.output.txt && \
    python3.7 linked_maps_to_osm.py -g maps/line_seg.geom.jl -f railway 2>&1 | tee maps/osm.output.txt && \
    python3.7 generate_graph.py -g maps/line_seg.geom.jl -s maps/line_seg.seg.jl -r maps/line_seg.rel.jl -l maps/line_seg.geom.osm.jl -o maps/linked_maps.maps.ttl && \
    ls -l maps
