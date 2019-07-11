# json
import json
# rdflib
import rdflib
from rdflib import BNode, URIRef, Literal, XSD, Namespace, RDF, RDFS

# TODO: use geo
LMG = Namespace('http://isi.linkedmap.com/_')
GEO = Namespace('http://www.opengis.net/ont/geosparql#')
SCHEMA = Namespace('http://schema.org/')

def read_WKT_literals(csv_file_name):
    global gid_to_wkt
    read_file = open(csv_file_name, "r")
    for line_r in read_file:
        temp_dict_in = json.loads(line_r)
        gid = temp_dict_in['gid']
        wkt_ms = temp_dict_in['wkt']
        gid_to_wkt[gid] = wkt_ms

class LinkedMapGraph:
    def __init__(self):
        self.data_triples = rdflib.Graph()
        self.data_triples.bind('lmg', LMG)
        self.data_triples.bind('geo', GEO)
        self.data_triples.bind('schema', SCHEMA)

    def add_map(self, map_id, map_name, map_gid, is_leaf):
        global gid_to_wkt
        map_uri = URIRef(LMG[str(map_id)])
        map_spatial_cov_uri = URIRef(LMG[map_name.lower() + '_' + str(map_id) + '_sc'])
        self.data_triples.add((map_uri, RDF.type, SCHEMA['Map']))
        self.data_triples.add((map_spatial_cov_uri, RDF.type, SCHEMA['GeoShape']))
        self.data_triples.add((map_uri, SCHEMA['spatialCoverage'], map_spatial_cov_uri))
        if True == is_leaf:
            # TODO: fix is_leaf modeling
            self.data_triples.add((map_uri, SCHEMA['isLeaf'], Literal(True, datatype=XSD.boolean)))
        # TODO: fix metadata representation
        self.data_triples.add((map_uri, SCHEMA['mapType'], Literal(map_name[1:-1], datatype=XSD.integer)))
        if map_gid in gid_to_wkt:
            # TODO: map_spatial_cov_uri was map_uri
            self.data_triples.add((map_spatial_cov_uri, SCHEMA['line'], Literal(gid_to_wkt[map_gid])))

    def add_map_child_to_parent(self, parent_map_id, child_map_id):
        parent_map_uri = URIRef(LMG[str(parent_map_id)])
        child_map_uri = URIRef(LMG[str(child_map_id)])
        self.data_triples.add((parent_map_uri, SCHEMA['hasPart'], child_map_uri))

    def add_map_sameas_relations(self, first_map_id, second_map_id):
        map_1_uri = URIRef(LMG[str(first_map_id)])
        map_2_uri = URIRef(LMG[str(second_map_id)])
        self.data_triples.add((map_1_uri, SCHEMA['sameAs'], map_2_uri))
        self.data_triples.add((map_2_uri, SCHEMA['sameAs'], map_1_uri))

try:
    gid_to_wkt = dict()
    read_WKT_literals("/tmp/geom.csv")

    # initialize graph
    lnkd_mp_grph = LinkedMapGraph()
    
    # read file: map.csv
    read_file = open("/tmp/map.csv", "r")
    for line_r in read_file:
      temp_dict_in = json.loads(line_r)
      map_id = temp_dict_in['id']
      map_line_name = temp_dict_in['line_name']
      map_gid = temp_dict_in['gid']
      map_is_leaf = temp_dict_in['isleaf']
      lnkd_mp_grph.add_map(map_id, map_line_name, map_gid, map_is_leaf)

    # read file: contain.csv
    read_file = open("/tmp/contain.csv", "r")
    for line_r in read_file:
      temp_dict_in = json.loads(line_r)
      map_par_id = temp_dict_in['par_id']
      map_chi_id = temp_dict_in['child_id']
      lnkd_mp_grph.add_map_child_to_parent(map_par_id, map_chi_id)

    # read file: sameas.csv
    read_file = open("/tmp/sameas.csv", "r")
    for line_r in read_file:
      temp_dict_in = json.loads(line_r)
      map_1_id = temp_dict_in['id1']
      map_2_id = temp_dict_in['id2']
      lnkd_mp_grph.add_map_sameas_relations(map_1_id, map_2_id)

finally:
    lnkd_mp_grph.data_triples.serialize("lnkd_mp_grph.ttl", format="turtle")
    print("Done...")