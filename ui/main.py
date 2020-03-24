from argparse import ArgumentParser
from baselutils import fclrprint
from datetime import datetime
from flask import Flask, request, render_template, url_for
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)

CQUERY = 'chosen_query'
SPARQL_PREFIXES = """
prefix geom: <http://data.ign.fr/def/geometrie#>
prefix dcterms: <http://purl.org/dc/terms/>
prefix geo: <http://www.opengis.net/ont/geosparql#>
prefix lmg: <http://linkedmaps.isi.edu/>
prefix prov: <http://www.w3.org/ns/prov#>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix xml: <http://www.w3.org/XML/1998/namespace>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix geovm: <http://geovocab.org/geometry#>
prefix ogc: <http://www.opengis.net/ont/geosparql#>
"""
SPARQL_EXAMPLES =  {
'': '',
'1 edition': '''
SELECT ?f ?wkt
WHERE {
  ?f a geo:Feature ;
     geo:hasGeometry [ geo:asWKT ?wkt ] ;
     dcterms:date "1962-01-01T00:00:00"^^xsd:dateTime .
  FILTER NOT EXISTS { ?f geo:sfContains _:_ }
}
''',
'1 edition - unique': '''
SELECT ?f ?wkt
WHERE {
  ?f a geo:Feature ;
     geo:hasGeometry [ geo:asWKT ?wkt ] ;
     dcterms:date "1962-01-01T00:00:00"^^xsd:dateTime ;
  FILTER NOT EXISTS { ?f geo:sfContains _:_ }
  ?f dcterms:date ?date .
}
GROUP BY ?f ?wkt
HAVING (COUNT(DISTINCT ?date) = 1)
''',
'2 editions - similar': '''
SELECT ?f ?wkt
WHERE {
  ?f a geo:Feature ;
     geo:hasGeometry [ geo:asWKT ?wkt ] ;
     dcterms:date "1962-01-01T00:00:00"^^xsd:dateTime ;
     dcterms:date "2001-01-01T00:00:00"^^xsd:dateTime .
  FILTER NOT EXISTS { ?f geo:sfContains _:_ }
}
''',
'2 editions - difference': '''
SELECT ?f ?wkt
WHERE {
  ?f a geo:Feature ;
     geo:hasGeometry [ geo:asWKT ?wkt ] ;
     dcterms:date "1962-01-01T00:00:00"^^xsd:dateTime .
  FILTER NOT EXISTS { ?f geo:sfContains _:_ }
  MINUS { ?f dcterms:date "2001-01-01T00:00:00"^^xsd:dateTime . }
}
''',
'2 editions - similar - LinkedGeoData': '''
SELECT ?f ?lgd_inst ?wkt
WHERE {
  ?f a geo:Feature ;
     dcterms:date "1962-01-01T00:00:00"^^xsd:dateTime ;
     dcterms:date "2001-01-01T00:00:00"^^xsd:dateTime ;
     geo:sfOverlaps ?lgd_inst .
  FILTER NOT EXISTS { ?f geo:sfContains _:_ }
  SERVICE <http://linkedgeodata.org/sparql> {
     ?lgd_inst geovm:geometry [ ogc:asWKT ?wkt ] .
  }
}
'''}

###################################################################################################

@app.route('/', methods=['GET'])
def query_preload():
    cquery = ''
    if CQUERY in request.args:
        cquery = request.args.get(CQUERY)
    rquery = SPARQL_EXAMPLES[cquery]
    return render_template('index.html', classdropdown=SPARQL_EXAMPLES.keys(), selectedclass=cquery,
                           raw_sparql=rquery, data=list())

@app.route('/', methods=['POST'])
def query():
    global g_sparql

    # read the posted values from the UI
    _sparql = request.form['sparql']
    if _sparql:
        g_sparql.setQuery(SPARQL_PREFIXES + _sparql)
        results = g_sparql.query().convert()
        ret = list()
        linestring_data = list()
        try:
            keys = results["results"]["bindings"][0].keys()
            for i in range(len(results["results"]["bindings"])):
                re = list()
                for k in keys:
                    res = results["results"]["bindings"][i][k]['value']
                    re.append(res)
                    if k == 'wkt':
                        linestring_data.append(res)
                ret.append(re)
        except:
            keys = ['No results']
        return render_template('index.html', classdropdown=SPARQL_EXAMPLES.keys(), selectedclass='',
                               raw_sparql=_sparql, data=linestring_data, key=keys, result=ret)

if __name__ == '__main__':
  global g_sparql

  parser = ArgumentParser()
  parser.add_argument('-s')
  args = parser.parse_args()
  app.config['sparql_endpoint'] = "http://localhost:3030/linkedmaps/query"
  if args.s:
    app.config['sparql_endpoint'] = args.s
  else:
    fclrprint(f'---You did not set a SPARQL endpoint, using default', 'r')
  fclrprint(f'---Your SPARQL endpoint: {app.config["sparql_endpoint"]}', 'g')
  g_sparql = SPARQLWrapper(app.config['sparql_endpoint'])
  g_sparql.setReturnFormat(JSON)
  app.run(host="localhost", port=5000, debug=True)