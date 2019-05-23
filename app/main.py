from flask import Flask, request, render_template, url_for
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)
sparql = SPARQLWrapper("http://localhost:3030/spatial_data/sparql")
sparql.setReturnFormat(JSON)

SPARQL_PREFIXES = """
            prefix spatial: <http://jena.apache.org/spatial#>
            prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix schema: <http://schema.org/>
            prefix xml: <http://www.w3.org/XML/1998/namespace>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
            prefix wkt: <http://www.opengis.net/ont/geosparql#>
            """

def generate_query_by_sequence_string(sequence_string):
    SPARQL_Q_EMB = ""
    num_of_terms = len(sequence_string.split(','))
    for uri_idx_counter, uri_idx in enumerate(sequence_string.split(',')):
        if uri_idx_counter != 0:
            SPARQL_Q_EMB += "|| "
        SPARQL_Q_EMB += "?x = <http://isi.linkedmap.com/_%d> " % int(uri_idx)
    SPARQL_Q_FULL = """
    SELECT ?wkt
    WHERE {
       FILTER (%s)
       ?x rdf:type schema:Map ;
             schema:spatialCoverage [ schema:line ?wkt ] .
    }
    """ % SPARQL_Q_EMB
    return SPARQL_Q_FULL

def get_linestring_data_by_sparql(sparql_query_in_text):
    sparql.setQuery(SPARQL_PREFIXES + sparql_query_in_text)
    results = sparql.query().convert()
    keys = results["results"]["bindings"][0].keys()
    int_results = results["results"]["bindings"]
    linestring_data = list()
    for i in range(len(int_results)):
        for k in int_results[i]:
            # TODO: compare int_results[i][k]['datatype'] == 'http://www.opengis.net/ont/geosparql#wktLiteral'
            linestring_data.append(int_results[i][k]['value'])
    return linestring_data

@app.route("/")
def home():
    SPARQL_Q = generate_query_by_sequence_string("1")
    default_data = get_linestring_data_by_sparql(SPARQL_Q)
    return render_template('index.html', data = default_data)

@app.route("/sparqlex")
def sparqlex():
    segs_seq_str = "1"
    if "seq_str" in request.args:
        segs_seq_str = request.args.get("seq_str")
    SPARQL_Q = generate_query_by_sequence_string(segs_seq_str)
    linestr_data = get_linestring_data_by_sparql(SPARQL_Q)
    return render_template('index.html', data = linestr_data)

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)