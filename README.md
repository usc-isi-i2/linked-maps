# Linked Maps Project

A framework to convert vector data extracted from multiple historical maps into linked spatio-temporal data.
The resulting RDF graphs can be queried and visualized to understand the changes in specific regions through time.

The process is separated into three steps:

1. Automatic line segmentation using `PostgreSQL` (with `Postgis` extension and integration using `Python`). Follow README in directory `line_segmentation/`.
2. Modeling the data into RDF. Follow README in directory `gen_ttl_from_csv/`.
3. Running queries using `SPARQL` on Apache Jena. Follow the README in directory `query_and_viz/` (See README in directory `app/` for a mock-up of our front-end).