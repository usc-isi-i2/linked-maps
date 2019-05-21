# Modeling the data into RDF

Prior to this step, the user most export the data from the `PostgreSQL` DB tables (with `csv` extensions) into a sub-directory named `test_lm` in this directory.
The script `construct_triples.py` processes the files and generates the file `nkd_mp_grph.ttl` which contains the required RDF we should upload later to Apache Jena.

How to run:
```
python construct_triples.py
```