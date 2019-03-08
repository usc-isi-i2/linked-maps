# Model the data from DB
For Windows
1) Install Karma https://github.com/usc-isi-i2/Web-Karma/wiki/Installation%3A-One-Click-Install
2) Install PostGis JDBC https://github.com/usc-isi-i2/Web-Karma/issues/362. If not work, place .JAR to ```/path/to/Karma/resources/app/tomcat/lib``` instead
3) Import data from PostgreSQL https://github.com/usc-isi-i2/Web-Karma/wiki/Importing-Data. The default port is 5432.
4) Import the models

# Model the data from DB (Batch Mode)
For Windows
1) Download Karma Source and follow the installation instruction from https://github.com/usc-isi-i2/Web-Karma/wiki/Installation%3A-Source-Code 
2) Navigate to ```\Web-Karma-master\karma-offline``` and run ``` mvn install -P shaded```
3) Navigate to target folder  ```\Web-Karma-master\karma-offline\target.``` 
4) Download PostgreSQL JDBC driver https://jdbc.postgresql.org/download.html and place it in the target folder.  
5) Download public.maps-model.ttl and place it in the target folder
6) Run this command;

```
java -cp "postgresql-42.2.5.jre7.jar;karma-offline-0.0.1-SNAPSHOT-shaded.jar" edu.isi.karma.rdf.OfflineRdfGenerator --sourcetype DB --dbtype PostGIS --hostname localhost --username <your_user_name> --password <your_password> --portnumber 5432 --dbname <your_db_name> --tablename maps --modelfilepath public.maps-model.ttl --outputfile out.ttl
```

Once you have already set up, the next time you just navigate to ```\Web-Karma-master\karma-offline\target.``` , and do step 5) and 6).

Note: You must replace the table name ```<map_table_name```, ```<geom_table_name>```, ```<same_as_table_name>```, ```contain_table_name``` in the models ttl file in accordance with your [config file](https://github.com/usc-isi-i2/linked-maps/blob/master/1%20-%20Line%20Segmentation%20(Python%2BPostgis)/config.json)
