FROM ubuntu:16.04
LABEL Author="Vasu Jain" Email="vasu.jain@isi.edu"

# Set the working directory to /linked-maps
WORKDIR /linked-maps

# install python3.6 and wget
RUN apt-get update && \
    apt-get install -y software-properties-common wget && \
    add-apt-repository -y ppa:jonathonf/python-3.6
RUN apt-get update -y
RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv

# update pip and install rdflib
RUN python3.6 -m pip install pip --upgrade
RUN pip install setuptools
RUN pip install rdflib

# install GDAL/OGR
RUN add-apt-repository -y ppa:ubuntugis/ppa && \
    apt-get update -y && \
    apt-get install -y gdal-bin libgdal-dev python-gdal python3-gdal

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt xenial-pgdg main" >> /etc/apt/sources.list'
RUN wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -
RUN apt update
RUN apt install -y postgresql-10
RUN apt install -y postgresql-10-postgis-2.4 
RUN apt install -y postgresql-10-postgis-scripts

#to get the commandline tools shp2pgsql, raster2pgsql you need to do this
RUN apt install -y postgis
RUN pip install psycopg2

# Make port 80 available to the world outside this container
EXPOSE 3030 5432

# Define environment variable
ENV NAME LinkedMaps

COPY . /linked-maps

# Run  when the container launches
CMD ["echo", "done"]