# knowledge graph of historical map data

## URI of vector data

python code

    from zlib import crc32
    wkt = getValue('geom')
    return hex(crc32(wkt))[2:]

## from postGIS to karma

<http://usc-isi-i2.github.io/karma/>

### ontology

The ontology we use for now is from <http://schema.org>.

TODO: The ontology isn't 100% suitable for our project, maybe we can create our own ontology.

### file format

PostgreSQL is a relational database, data stores in tables.

We use PostGIS to generate csv file and load in Karma.

### model

* schema:Map --> vector
* schema:MapCategoryType --> map

### csv and model examples

#### map

map|year|scale|source
---|---|---|---
A|2005|1:10000|USGS

* schema:MapType
  * URI  A
  * schema:ReleaseDate 2005
  * schema:scale 1:10000
  * schema:source USGS

#### vector

URI|map|geom
---|---|---
2wqfg32|A|geometry in WKT format

* schema:Map
  * URI: 2wqfg32
  * schema:geo WKT string
  * schema:mapType MapCategoryType1

* MapCategoryType1
  * URI: A

#### contains(vector relationship)

URI|partURI
---|---
2wqfg32|srt46we

* schema:Map
  * URI: 2wqfg32
  * schema:hasPart Map2

* Map2
  * URI srt46we

#### sameAs(vector relationship)

URI|sameAsURI
---|---
2wqfg32|ertu544

* schema:Map
  * URI: 2wqfg32
  * schema:sameAs Map2

* Map2
  * URI ertu544

## using Apache Jena

### why

Geometry is very long for some vectors, and Karma built-in rdf query engine OPEN-RDF can't support that.

### setup Jena and fuseki

follow the instruction <https://jena.apache.org/documentation/fuseki2/index.html>

Run

    ./fuseki-server

Then testing everything in <localhost:3030>

### from Karma to Jena

After modeling in Karma, we can generate ttl files based on our model, just load them into Jena, then query in Jena

## Queries

### vectors in 2003 and not in 2005

    PREFIX schema: <http://schema.org/>
    select distinct ?a ?mapa
    where{
        ?a schema:geo ?geo.
        ?a schema:mapType ?mapa .
        ?mapa schema:releaseDate "2003" .
        filter not exists{
            ?a schema:sameAs ?b.
            ?b schema:mapType ?mapb .
            ?mapb schema:releaseDate "2005" .
        }
        minus{
            ?a schema:hasPart ?x
        }
    }

### vectors in 2003 and 2005

    PREFIX schema: <http://schema.org/>
    select distinct ?a
    where{
        ?a schema:geo ?geo.
        ?a schema:mapType ?mapa .
        ?mapa schema:releaseDate "2003" .
        ?b schema:mapType ?mapb .
        ?mapb schema:releaseDate "2005" .
        ?a schema:sameAs ?b .
    }