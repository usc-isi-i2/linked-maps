# Model the data from DB
For Windows
1) Install Karma https://github.com/usc-isi-i2/Web-Karma/wiki/Installation%3A-One-Click-Install
2) Install PostGis JDBC https://github.com/usc-isi-i2/Web-Karma/issues/362. If not work, place .JAR to ```/path/to/Karma/resources/app/tomcat/lib instead```
3) Import data from PostgreSQL https://github.com/usc-isi-i2/Web-Karma/wiki/Importing-Data. The default port is 5432.
4) Import the models

# Model the data from DB (Batch Mode)
For Windows
1) Download Karma Source and follow the instruction https://github.com/usc-isi-i2/Web-Karma/wiki/Installation%3A-Source-Code#compiling-and-installing-karma-in-offline-mode
2) Follow this instruction for offline RDF generator https://github.com/usc-isi-i2/Web-Karma/wiki/Batch-Mode-for-RDF-Generation#offlinerdfgenerator. Navigate to ```Web-Karma-master\karma-offline\target.``` Then, download PostgreSQL JDBC driver https://jdbc.postgresql.org/download.html and place it in the target folder.  Run this command;

```
java -cp "postgresql-42.2.5.jre7.jar;karma-offline-0.0.1-SNAPSHOT-shaded.jar" edu.isi.karma.rdf.OfflineRdfGenerator --sourcetype DB --dbtype PostGIS --hostname localhost --username <your_user_name> --password <your_password> --portnumber 5432 --dbname <your_db_name> --tablename maps --modelfilepath public.maps-model.ttl --outputfile out.ttl
```
