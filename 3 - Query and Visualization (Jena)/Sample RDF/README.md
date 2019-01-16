1) Query 1 - RDF file Hang used during development
2) Query 2 - One sample tripple from [out.ttl](https://github.com/usc-isi-i2/linked-maps/blob/master/2%20-%20RDF%20(Karma)/out.ttl).
Note: Right now we cannot use output from Karam directly. We have to do two things;
1. add ```@prefix wkt: <http://www.opengis.net/ont/geosparql#> .```
2. change from 
```<http://localhost:8080/source/43ab5efc> <http://schema.org/geo> "MULTILINESTRING((...))" .```
to 
```<http://localhost:8080/source/43ab5efc> wkt:asWKT "MULTILINESTRING((...))"^^wkt:wktLiteral .```

