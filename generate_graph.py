# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from os.path import basename
from datetime import datetime
from json import loads
from mykgutils import fclrprint
from rdflib import Graph, URIRef, Literal, XSD, Namespace, RDF

LMG = Namespace('http://isi.linkedmap.com/')
GEO = Namespace('http://www.opengis.net/ont/geosparql#')
PROV = Namespace('http://www.w3.org/ns/prov#')
DCTERMS = Namespace('http://purl.org/dc/terms/')

class LinkedMapGraph:
  ''' A graph holding the nodes and relations of the pre-processed maps. '''

  def __init__(self, json_file_name):
    ''' Init the linked map graph and read the WKT literals file,
    and map each gid to its WKT literal. '''

    self.dt = Graph()
    self.dt.bind('lmg', LMG)
    self.dt.bind('geo', GEO)
    self.dt.bind('prov', PROV)
    self.dt.bind('dcterms', DCTERMS)
    self.gid2wkt = dict()
    with open(json_file_name, "r") as read_file:
      for line_r in read_file:
        gid_wkt_entry = loads(line_r)
        self.gid2wkt[gid_wkt_entry['gid']] = gid_wkt_entry['wkt']

  def add_geo_feature_node(self, segment_gid, segment_name, segment_years):
    ''' Add a segment to the graph '''

    # geo:Feature
    # TODO: need to hash the URI
    seg_feat_uri = URIRef(LMG[str(segment_gid)])
    self.dt.add((seg_feat_uri, RDF.type, GEO['Feature']))

    # geo:Geometry
    seg_geo_uri = URIRef(LMG[str(segment_gid) + '_sc_' + segment_name.lower()])
    self.dt.add((seg_geo_uri, RDF.type, GEO['Geometry']))

    # geo:Feature --geo:hasGeometry--> geo:Geometry
    self.dt.add((seg_feat_uri, GEO['hasGeometry'], seg_geo_uri))

    # --dcterms:created--> LITERAL^^xsd:dateTime
    d_now = datetime.today()
    self.dt.add((seg_feat_uri, DCTERMS['created'], Literal(d_now.isoformat(), datatype=XSD.dateTime)))

    # --dcterms:date--> LITERAL^^xsd:dateTime
    for seg_yr in segment_years:
      seg_yr_dt_obj = datetime.strptime(str(seg_yr), '%Y')
      self.dt.add((seg_feat_uri, DCTERMS['date'], Literal(seg_yr_dt_obj.isoformat(), datatype=XSD.dateTime)))

    # --geo:asWKT--> "<http://www.opengis.net/def/crs/OGC/1.3/CRS84> LITERAL"^^geo:wktLiteral
    # TODO: add CRS94 prefix
    self.dt.add((seg_geo_uri, GEO['asWKT'], Literal(self.gid2wkt[segment_gid], datatype=GEO['wktLiteral'])))
    # TODO: add provenance information
    #   --prov:wasGeneratedBy--> prov:Activity
    #     --prov:wasAssociatedWith--> foaf:Organization, prov:Agent
    # TODO: add Reverse Geocoding
    # TODO: add Positional Accuracy (buff)

  def add_geo_child_to_parent(self, parent_geo_feat_id, child_geo_feat_id):
    ''' Link a child segment to its parent segment. '''

    parent_geo_feat_uri = URIRef(LMG[str(parent_geo_feat_id)])
    child_geo_feat_uri = URIRef(LMG[str(child_geo_feat_id)])

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

def main():

  ap = ArgumentParser(description='Process line segmetation output files (jl) and generate (ttl) file containing triples.\n\tUSAGE: python %s -g GEOMETRY_FILE -s SEGMENTS_FILE -r RELATIONS_FILE' % (basename(__file__)))
  ap.add_argument('-g', '--geometry_file', help='File (jl) holding the geometry info.', type=str)
  ap.add_argument('-s', '--segments_file', help='File (jl) holding th relations info (parents, children).', type=str)
  ap.add_argument('-r', '--relations_file', help='File (jl) holding th relations info (parents, children).', type=str)
  ap.add_argument('-o', '--output_file', help='The output file (ttl) with the generated triples.', default='lm_graph.ttl', type=str)

  args = ap.parse_args()

  if args.geometry_file and args.relations_file and args.segments_file:
      fclrprint('Going to process files %s, %s, %s...' % (args.geometry_file, args.segments_file, args.relations_file))
      
      # initialize graph with gid-to-wkt mapping file
      lm_graph = LinkedMapGraph(args.geometry_file)

      # load segments info
      with open(args.segments_file) as read_file:
        for line_r in read_file:
          seg_dict = loads(line_r)
          lm_graph.add_geo_feature_node(seg_dict['gid'], seg_dict['name'], seg_dict['years'])

      # load relations info
      with open(args.relations_file) as read_file:
        for line_r in read_file:
          rel_dict = loads(line_r)
          lm_graph.add_geo_child_to_parent(rel_dict['parent_gid'], rel_dict['child_gid'])

      # materialize triples
      lm_graph.dt.serialize(args.output_file, format="turtle")
      fclrprint('Done, generated ttl file %s!' % (args.output_file), 'g')
  else:
      fclrprint('Geometry, segments and relations files were not provided.', 'r')
      exit(1)

if __name__ == '__main__':
    main()