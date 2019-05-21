# Modeling data in RDF

Prior to this step, the user most export the data from the PostgreSQL DB tables (Postgis) into a directory named ```test_lm``` in this directory with ```csv``` extension.
The script ```construct_triples.py``` processes the files and generates the file ```lnkd_mp_grph.ttl``` which contains the required RDF.

How to run:
```
python construct_triples.py
```