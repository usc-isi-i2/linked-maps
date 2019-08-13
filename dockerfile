FROM ubuntu:16.04
LABEL Author="Vasu Jain" Email="vasu.jain@isi.edu"

# Set the working directory to /linked-maps
WORKDIR /linked-maps

# install python3.6 and wget
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
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt xenial-pgdg main" >> /etc/apt/sources.list' &&\
    wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add - &&\
    apt-get update &&\
    apt-get install -y postgresql-11 &&\
    apt-get install -y postgresql-11-postgis-2.5 &&\ 
    apt-get install -y postgresql-11-postgis-scripts &&\
    apt-get install -y postgis

# update pip and install rdflib
RUN python3.5 -m pip install pip --upgrade &&\
    pip install setuptools rdflib psycopg2-binary

# Make port 5432 available to the world outside this container
EXPOSE 5432

# Define environment variable
ENV NAME LinkedMaps

# COPY line_segmentation and construct_triples to linked-maps
COPY ./line_segmentation /linked-maps
COPY ./gen_ttl_from_csv/construct_triples.py /linked-maps

USER postgres

# TODO: run the following inside the container as postgres user:
# 1. `/etc/init.d/postgresql start && createdb linkedmaps && psql linkedmaps -c "CREATE EXTENSION Postgis;"` 