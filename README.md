# Linked Maps Project

A framework to convert vector data extracted from multiple historical maps into linked spatio-temporal data.
The resulting RDF graphs can be queried and visualized to understand the changes in specific regions through time.

The process can is separated into three steps:

1. Automated Line Segmentation using PostgreSQL and Postgis (Python). See README in directory ```line_segmentation/```.
2. Model data in RDF. See README in directory ```gen_ttl_from_csv/```.
3. Perfrom query using SPARQL on Apache Jena. See README in directory ```query_and_viz/``` and directory ```app/``` for a mock-up of our Front-End.