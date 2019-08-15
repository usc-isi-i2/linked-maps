FROM ubuntu:16.04
MAINTAINER Basel Shbita "shbita@usc.edu"

# Set the working directory to /linked-maps
WORKDIR /linked-maps

# install python3.5 and wget
RUN apt-get update && \
    apt-get install -y software-properties-common wget && \
    add-apt-repository -y ppa:jonathonf/python-3.5
RUN apt-get update -y
RUN apt-get install -y build-essential python3.5 python3.5-dev python3-pip python3.5-venv

# install GDAL/OGR
RUN add-apt-repository -y ppa:ubuntugis/ppa && \
    apt-get update -y && \
    apt-get install -y gdal-bin libgdal-dev python-gdal python3-gdal

# install postgresql and postgis
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt xenial-pgdg main" >> /etc/apt/sources.list' && \
    wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y postgresql-11 && \
    apt-get install -y postgresql-11-postgis-2.5 && \ 
    apt-get install -y postgresql-11-postgis-scripts && \
    apt-get install -y postgis

# update pip
RUN python3.5 -m pip install pip --upgrade

# set working directory to /linked-maps
COPY ./ /linked-maps
WORKDIR /linked-maps

# install additional requirements
RUN pip3.5 install -r requirements.txt

# grant access to all users for 'results' dir
RUN chmod 777 results

# switch to user 'postgres'
USER postgres

# initiate postgresql service and create database with postgis extension
# then run line-segmentation and generate triples
CMD /etc/init.d/postgresql start && \
    createdb linkedmaps && \
    psql linkedmaps -c "CREATE EXTENSION Postgis;" && \
    python3.5 main.py -d maps -c config.json -r -o results/line_seg.jl && \
    python3.5 generate_graph.py -g results/line_seg.geom.jl -s results/line_seg.seg.jl -r results/line_seg.rel.jl -o results/linked_maps_graph.ttl && \
    ls -l results
