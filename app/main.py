from flask import Flask, request, render_template, url_for
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)
sparql = SPARQLWrapper("http://localhost:3030/spatial_data/sparql")
sparql.setReturnFormat(JSON)

SPARQL_PREFIXES = """
            prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix schema: <http://schema.org/>
            prefix xml: <http://www.w3.org/XML/1998/namespace>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
            prefix wkt: <http://www.opengis.net/ont/geosparql#>
            """

SPARQL_EXAMPLE = """
            SELECT ?wkt
            WHERE {
              <http://localhost:8080/source/%s> schema:includesObject ?thing .
              ?thing wkt:asWKT ?wkt ;
            }
            """

@app.route("/")
def home():
    data = ['LINESTRING(34.79011521585437 32.11589598470496,34.78736863382312 32.06470337558891)', \
            'LINESTRING(34.93019089944812 32.20192792321161,35.13618455179187 32.16705989986249)']
    return render_template('index.html', data = data)

@app.route("/sparqlex")
def sparqlex():
    map_id = "4"
    if "id" in request.args:
        map_id = request.args.get("id")
    sparql.setQuery(SPARQL_PREFIXES + SPARQL_EXAMPLE % (map_id))
    results = sparql.query().convert()
    keys = results["results"]["bindings"][0].keys()
    int_results = results["results"]["bindings"]
    linestring_data = list()
    for i in range(len(int_results)):
        for k in int_results[i]:
            # TODO: compare int_results[i][k]['datatype'] == 'http://www.opengis.net/ont/geosparql#wktLiteral'
            linestring_data.append(int_results[i][k]['value'])
    return render_template('index.html', data = linestring_data)

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)