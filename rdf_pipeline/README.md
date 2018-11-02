## Setting Up Environment

### Karma

1. Installing Karma using the tutorial: [Installation: Source Code](https://github.com/usc-isi-i2/Web-Karma/wiki/Installation%3A-Source-Code)
2. [Building the karma-offline JAR](https://github.com/usc-isi-i2/Web-Karma/wiki/Batch-Mode-for-RDF-Generation)

### Apache Jena

1. Download the Apache Jena Fuseki from https://jena.apache.org/download/#apache-jena-fuseki
2. Download [jts-1.14.jar](https://github.com/usc-isi-i2/linked-maps/blob/master/rdf_pipeline/jts-1.14.jar) and move it to your `apache-jena-fuseki/lib` directory (If `lib/` not exists, create one)
3. Jena database configuration file: download [spatial_data.ttl](https://github.com/usc-isi-i2/linked-maps/blob/master/rdf_pipeline/spatial_data.ttl), modify the following lines to your own path:
```
<#dataset> rdf:type      tdb:DatasetTDB ;
    tdb:location "/YOURPATH/apache-jena-fuseki-X.X.X/run/databases/spatial_data"     .
    
spatial:directory <file:/YOURPATH/apache-jena-fuseki-X.X.X/run/databases/spatial_data/spatial> ;
```

Then move the file to the directory `apache-jena-fuseki-X.X.X/run/configuration`

4. Run the following command to start Jena Fuseki:
```
java -cp "fuseki-server.jar:lib/jts-1.14.jar" org.apache.jena.fuseki.cmd.FusekiCmd -debug
```
