from SPARQLWrapper import SPARQLWrapper, JSON
from pandas import DataFrame

LCL_ENDPOINT = "http://localhost:3030/linkedmaps/query"
LGD_ENDPOINT = "http://linkedgeodata.org/sparql"

SPARQL_HEADER = """
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


def get_local_gid_df(gid):
  sparql = SPARQLWrapper(LCL_ENDPOINT)

  query_str = SPARQL_HEADER + '''
    SELECT ?f ?wkt
    WHERE {
      ?f a geo:Feature ;
         geo:hasGeometry [ geo:asWKT ?wkt ] .
      FILTER (?f = <http://linkedmaps.isi.edu/%d>)
    }
  ''' % (gid)

  #  set format and trigger query
  sparql.setQuery(query_str)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()

  df = DataFrame(columns=['GID', 'Instance', 'Coordinates', 'Label', 'Types'])

  if 'results' in results and \
     'bindings' in results['results'] and \
     len(results['results']['bindings']) != 0:
    for result in results['results']['bindings']:
      if 'f' in result and \
         'wkt' in result:
        df = df.append({'GID': result['f']['value'], \
                        'Instance': None, \
                        'Coordinates':  result['wkt']['value'], \
                        'Label': None, \
                        'Types': None}, \
                        ignore_index=True)

  return df


def get_osm_df(gid):
  sparql = SPARQLWrapper(LCL_ENDPOINT)

  query_str = SPARQL_HEADER + '''

    SELECT ?f ?lgd_inst ?wkt ?label (group_concat(?lgd_type) as ?lgd_types)
    WHERE {
      ?f a geo:Feature ;
         geo:sfOverlaps ?lgd_inst .
      FILTER (?f = <http://linkedmaps.isi.edu/%d>)
      SERVICE <http://linkedgeodata.org/sparql> {
        ?lgd_inst geovm:geometry [ ogc:asWKT ?wkt ] ;
                  a ?lgd_type ;
                  rdfs:label ?label .
      }
    }
    GROUP BY ?f ?lgd_inst ?wkt ?label
  ''' % (gid)

  # set format and trigger query
  sparql.setQuery(query_str)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()

  df = DataFrame(columns=['GID', 'Instance', 'Coordinates', 'Label', 'Types'])

  if 'results' in results and \
     'bindings' in results['results'] and \
     len(results['results']['bindings']) != 0:
    for result in results['results']['bindings']:
      if 'f' in result and \
         'lgd_inst' in result and \
         'wkt' in result and \
         'label' in result and \
         'lgd_types' in result:
        df = df.append({'GID': result['f']['value'], \
                        'Instance': result['lgd_inst']['value'], \
                        'Coordinates':  result['wkt']['value'], \
                        'Label': result['label']['value'], \
                        'Types': result['lgd_types']['value']}, \
                        ignore_index=True)

  return df
