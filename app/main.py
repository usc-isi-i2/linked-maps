from flask import Flask, request, render_template, url_for
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

app = Flask(__name__)
sparql = SPARQLWrapper("http://localhost:3030/spatial_data/sparql")
sparql.setReturnFormat(JSON)

DEFAULT_TERM = "2000"

SPARQL_PREFIXES = """
prefix dcterms: <http://purl.org/dc/terms/>
prefix geo: <http://www.opengis.net/ont/geosparql#> 
prefix lmg: <http://isi.linkedmap.com/>
prefix prov: <http://www.w3.org/ns/prov#>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix xml: <http://www.w3.org/XML/1998/namespace>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
"""

SPARQL_BASE = """
SELECT ?f ?wkt
WHERE {
  ?f a geo:Feature ;
     dcterms:modified ?dtm ;
     dcterms:created ?dtc ;
     geo:hasGeometry [ geo:asWKT ?wkt ] .
  # select leaves only
  FILTER (?dtm = ?dtc)
  %s
}
GROUP BY ?f ?wkt
"""

def generate_query_by_sequence_string(sequence_string):
    SPARQL_ADD = "?f "
    num_of_terms = len(sequence_string.split(','))
    for term_idx, term in enumerate(sequence_string.split(',')):
        if term_idx != 0:
            SPARQL_ADD += "; \n     "
        # assume we work by years!
        date_dt_obj = datetime.strptime(term.strip(), '%Y')
        SPARQL_ADD += 'dcterms:date "%s"^^xsd:dateTime ' % (date_dt_obj.isoformat())
        if term_idx == (num_of_terms - 1):
            SPARQL_ADD += '.'
    FULL_SPARQL = SPARQL_BASE % SPARQL_ADD
    print(FULL_SPARQL)
    # TODO: to support the unique part of a map we must inforce
    #       a distinct number of triples. i.e.:
    #
    #       ?f dcterms:date ?date .
    #       HAVING (COUNT(DISTINCT ?date) = 1)
    #
    # TODO: to support the minus operator we must MINUS in SPARQL
    #
    #       MINUS { ?f dcterms:date "1980-01-01T00:00:00"^^xsd:dateTime . }
    return FULL_SPARQL

def get_linestring_data_by_sparql(sparql_query_in_text):
    sparql.setQuery(SPARQL_PREFIXES + sparql_query_in_text)
    results = sparql.query().convert()
    keys = results["results"]["bindings"][0].keys()
    int_results = results["results"]["bindings"]
    debug_uris = list()
    linestring_data = list()
    for res in int_results:
        debug_uris.append(res['f']['value'])
        linestring_data.append(res['wkt']['value'])
    print(debug_uris)
    return linestring_data

@app.route("/")
def home():
    SPARQL_Q = generate_query_by_sequence_string(DEFAULT_TERM)
    default_data = get_linestring_data_by_sparql(SPARQL_Q)
    return render_template('index.html', data = default_data)

@app.route("/sparqlex")
def sparqlex():
    segs_seq_str = DEFAULT_TERM
    if "seq_str" in request.args:
        segs_seq_str = request.args.get("seq_str")
    SPARQL_Q = generate_query_by_sequence_string(segs_seq_str)
    linestr_data = get_linestring_data_by_sparql(SPARQL_Q)
    return render_template('index.html', data = linestr_data)

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)