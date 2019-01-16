### Apache Jena Setting Up Environment

1. Download the Apache Jena Fuseki from https://jena.apache.org/download/#apache-jena-fuseki
2. Download [jts-1.14.jar](https://github.com/usc-isi-i2/linked-maps/blob/master/rdf_pipeline/jts-1.14.jar) and move it to your `apache-jena-fuseki/lib` directory (If `lib/` not exists, create one)
3. Jena database configuration file: download [spatial_data.ttl](https://github.com/usc-isi-i2/linked-maps/blob/master/rdf_pipeline/spatial_data.ttl), modify the following lines to your own path:
```
<#dataset> rdf:type      tdb:DatasetTDB ;
    tdb:location "/YOURPATH/apache-jena-fuseki-X.X.X/run/databases/spatial_data"     .
    
spatial:directory <file:/YOURPATH/apache-jena-fuseki-X.X.X/run/databases/spatial_data/spatial> ;
```

For example (Windows)
```
<#dataset> rdf:type      tdb:DatasetTDB ;
    tdb:location "C:/apache-jena-fuseki-3.9.0/run/databases/spatial_data"  
    
spatial:directory <file:../databases/spatial_data/spatial> ;
```

Then move the file to the directory `apache-jena-fuseki-X.X.X/run/configuration`

4. Run the following command to start Jena Fuseki:
```
java -cp "fuseki-server.jar:lib/jts-1.14.jar" org.apache.jena.fuseki.cmd.FusekiCmd -debug
```
For Windows:
```
java -cp ".\fuseki-server.jar;lib\jts-1.14.jar" org.apache.jena.fuseki.cmd.FusekiCmd
```
5. Open your browser and enter `http://localhost:3030/`
6. Manage datasets -> add new dataset -> create dataset
7. Select "upload data" on the dataset you created, and upload the RDF files
8. Now you can run SPARQL queries under "dataset" section.