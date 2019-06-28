from argparse import ArgumentParser
from datetime import datetime
from json import loads
from rdflib import Graph, URIRef, Literal, XSD, Namespace, RDF

LMG = Namespace('http://isi.linkedmap.com/')
GEO = Namespace('http://www.opengis.net/ont/geosparql#')
PROV = Namespace('http://www.w3.org/ns/prov#')
DCTERMS = Namespace('http://purl.org/dc/terms/')

def read_WKT_literals(csv_file_name):
  ''' Read the WKT literals and map each gid
  to its literal in a global dictionary g_gid_to_wkt. '''
  global g_gid_to_wkt
  read_file = open(csv_file_name, "r")
  for line_r in read_file:
      temp_dict_in = loads(line_r)
      gid = temp_dict_in['gid']
      wkt_ms = temp_dict_in['wkt']
      g_gid_to_wkt[gid] = wkt_ms

class LinkedMapGraph:
  ''' A graph holding the nodes and relations of the pre-processed maps. '''
  def __init__(self):
    ''' Init the linked map graph. '''
    self.dt = Graph()
    self.dt.bind('lmg', LMG)
    self.dt.bind('geo', GEO)
    self.dt.bind('prov', PROV)
    self.dt.bind('dcterms', DCTERMS)

  def add_geo_feature_node(self, segment_id, segment_name, segment_gid):
    ''' Add a map to the graph '''
    global g_gid_to_wkt
    # don't construct a blank node
    if segment_gid not in g_gid_to_wkt:
      return
    # geo:Feature
    # TODO: need to hash the URI
    seg_feat_uri = URIRef(LMG[str(segment_id)])
    self.dt.add((seg_feat_uri, RDF.type, GEO['Feature']))
    # geo:Geometry
    seg_geo_uri = URIRef(LMG[segment_name.lower() + '_' + str(segment_id) + '_sc'])
    self.dt.add((seg_geo_uri, RDF.type, GEO['Geometry']))
    # geo:Feature --geo:hasGeometry--> geo:Geometry
    self.dt.add((seg_feat_uri, GEO['hasGeometry'], seg_geo_uri))
    d_now = datetime.today()
    self.dt.add((seg_feat_uri, DCTERMS['created'], Literal(d_now.isoformat(), datatype=XSD.dateTime)))
    # --dcterms:date--> LITERAL^^xsd:dateTime
    #####################
    # TODO: fix
    date_lit = "1900"
    if '_line1' == segment_name:
      date_lit = '1980'
    elif '_line2' == segment_name:
      date_lit = '1990'
    elif '_line3' == segment_name:
      date_lit = '2000'
    date_lit_dt_obj = datetime.strptime(date_lit, '%Y')
    self.dt.add((seg_feat_uri, DCTERMS['date'], Literal(date_lit_dt_obj.isoformat(), datatype=XSD.dateTime)))
    ######################
    # --geo:asWKT--> "<http://www.opengis.net/def/crs/OGC/1.3/CRS84> LITERAL"^^geo:wktLiteral
    # TODO: add CRS94 prefix
    self.dt.add((seg_geo_uri, GEO['asWKT'], Literal(g_gid_to_wkt[segment_gid], datatype=GEO['wktLiteral'])))
    # TODO: add provenance information
    #   --prov:wasGeneratedBy--> prov:Activity
    #     --prov:wasAssociatedWith--> foaf:Organization, prov:Agent
    # TODO: add Reverse Geocoding
    # TODO: add Positional Accuracy

  def add_geo_child_to_parent(self, parent_geo_feat_id, child_geo_feat_id):
    ''' Link a child segment to its parent segment. '''
    parent_geo_feat_uri = URIRef(LMG[str(parent_geo_feat_id)])
    child_geo_feat_uri = URIRef(LMG[str(child_geo_feat_id)])
    # don't construct a blank node
    if (parent_geo_feat_uri, None, None) not in self.dt or \
      (child_geo_feat_uri, None, None) not in self.dt:
      return
    self.dt.add((parent_geo_feat_uri, GEO['sfContains'], child_geo_feat_uri))
    self.dt.add((child_geo_feat_uri, GEO['sfWithin'], parent_geo_feat_uri))
    # add dates of parent to its child
    for date in self.dt.objects(parent_geo_feat_uri, DCTERMS['date']):
      self.dt.add((child_geo_feat_uri, DCTERMS['date'], date))
    # when we discover a parent we must update its modified time to now
    # and update its child with created = modified
    #   leaf:  dcterms:created == dcterms:modified
    #   !leaf: dcterms:created != dcterms:modified
    d_now = datetime.today()
    self.dt.remove((parent_geo_feat_uri, DCTERMS['modified'], None))
    self.dt.add((parent_geo_feat_uri, DCTERMS['modified'], Literal(d_now.isoformat(), datatype=XSD.dateTime)))
    self.dt.remove((child_geo_feat_uri, DCTERMS['modified'], None))
    self.dt.add((child_geo_feat_uri, DCTERMS['modified'], Literal(d_now.isoformat(), datatype=XSD.dateTime)))
    self.dt.remove((child_geo_feat_uri, DCTERMS['created'], None))
    self.dt.add((child_geo_feat_uri, DCTERMS['created'], Literal(d_now.isoformat(), datatype=XSD.dateTime)))

  def add_geo_sameas_relations(self, first_geo_feat_id, second_geo_feat_id):
    ''' Create a sameas relation between two nodes in the graph '''
    geo_feat_1_uri = URIRef(LMG[str(first_geo_feat_id)])
    geo_feat_2_uri = URIRef(LMG[str(second_geo_feat_id)])
    # don't construct a blank node
    if (geo_feat_1_uri, None, None) not in self.dt or \
      (geo_feat_2_uri, None, None) not in self.dt:
      return
    self.dt.add((geo_feat_1_uri, GEO['sfEquals'], geo_feat_2_uri))
    self.dt.add((geo_feat_2_uri, GEO['sfEquals'], geo_feat_1_uri))

def main():

  global g_gid_to_wkt

  ap = ArgumentParser(description='TODO.\n\tUSAGE: TODO')
  ap.add_argument('-d', '--tables_dir', help='Directory where the (csv) tables files are stored (geom, map, contains, sameas).', default='data', type=str)
  ap.add_argument('-o', '--output_file', help='The output (ttl) file with the generated triples.', default='linked_maps_garph.ttl', type=str)

  args = ap.parse_args()

  g_gid_to_wkt = dict()
  read_WKT_literals(f'{args.tables_dir}/geom.csv')

  # initialize graph
  lnkd_mp_grph = LinkedMapGraph()
      
  # read file: map.csv
  read_file = open(f'{args.tables_dir}/map.csv', 'r')
  for line_r in read_file:
    temp_dict_in = loads(line_r)
    seg_id = temp_dict_in['id']
    seg_line_name = temp_dict_in['line_name']
    seg_gid = temp_dict_in['gid']
    lnkd_mp_grph.add_geo_feature_node(seg_id, seg_line_name, seg_gid)

  # read file: contain.csv
  read_file = open(f'{args.tables_dir}/contain.csv', 'r')
  for line_r in read_file:
    temp_dict_in = loads(line_r)
    seg_par_id = temp_dict_in['par_id']
    seg_chi_id = temp_dict_in['child_id']
    lnkd_mp_grph.add_geo_child_to_parent(seg_par_id, seg_chi_id)

  # read file: sameas.csv
  read_file = open(f'{args.tables_dir}/sameas.csv', 'r')
  for line_r in read_file:
    temp_dict_in = loads(line_r)
    seg_1_id = temp_dict_in['id1']
    seg_2_id = temp_dict_in['id2']
    lnkd_mp_grph.add_geo_sameas_relations(seg_1_id, seg_2_id)

  # serialize triples to 
  lnkd_mp_grph.dt.serialize(args.output_file, format="turtle")
  print(f'Done, created the ttl file {args.output_file} from table in directory {args.tables_dir}!')

if __name__ == '__main__':
    main()