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

# update pip and install rdflib
RUN python3.5 -m pip install pip --upgrade && \
    pip install setuptools rdflib psycopg2-binary

# set working directory to /linked-maps
COPY ./ /linked-maps
WORKDIR /linked-maps

# switch to user 'postgres'
USER postgres

# expose port 5432
# EXPOSE 5432
# createdb: could not connect to database template1: could not connect to server: No such file or directory
#    Is the server running locally and accepting
#    connections on Unix domain socket "/var/run/postgresql/.s.PGSQL.5432"?

# initiate postgresql service
RUN /etc/init.d/postgresql start

# create database with postgis extension
# RUN createdb linkedmaps
# RUN psql linkedmaps -c "CREATE EXTENSION Postgis;"
