# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import OrderedDict
from json import loads, dumps
from os.path import basename
from random import randint
from time import time, sleep
from re import sub as re_sub
from requests import get as get_request

# --- OSM API -----------------------------------------------------------------

def get_openstreetmap_member_uri(osm_type, osm_id):
    ''' Get OSM member LGD URI '''

    return "http://linkedgeodata.org/triplify/" + str(osm_type) + str(osm_id)

def query_osm_results(query_box = {'s':0,'n':0,'w':0,'e':0}, filter_tag = ''):
    ''' Query OSM 'relation' data elements in a given bounding box.
    'relation' elements are used to organize multiple nodes or ways into a larger whole.
    
    Generates an OSM http request and return response in JSON format.
    i.e. 
    http://overpass-api.de/api/interpreter?data=[out:json];node(41.5,-122.0,41.7,-121.6);%3C;out%20meta; '''

    query = "node({s},{w},{n},{e});<;out meta;".format(s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    ''' This call includes:
        - all nodes in the bounding box,
        - all ways that have such a node as member,
        - and all relations that have such a node or such a way as members. '''
    url = url_base + query
    try:
        sleep(2)
        req_start_time = time()
        osm_data = get_request(url).json()
        print('   Request took %.2f seconds' % (time() - req_start_time))
        if filter_tag != '':
            filtered_set = list()
            for itm in osm_data['elements']:
                if 'tags' in itm and filter_tag in itm['tags']:
                    filtered_set.append(itm)
            return filtered_set
        return osm_data['elements']        
    except ValueError as _:
        print('ValueError for query_box' + str(query_box))
        return []

def create_bounding_box(coordinates = [{'lat':0,'lng':0}], index = None, buffer = 0.001):
    ''' Create a bounding box given a set of latitude and longitude coordinates. '''

    if index is None:
        lat = [coord['lat'] for coord in coordinates]
        lng = [coord['lng'] for coord in coordinates]
        bbox = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    else:
        lat = coordinates[index]['lat']
        lng = coordinates[index]['lng']
        bbox = {'s':lat-buffer,'n':lat+buffer,'w':lng-buffer,'e':lng + buffer}
    return bbox

def get_openstreetmap_data(coordinates = [{'lat':0,'lng':0}], qkey='', samples=20):
    ''' Get OSM metadata in a given bounding box '''

    # get bbox that contains all of the coordinates
    bbox = create_bounding_box(coordinates, None)
    # print(f'bbox for the given set of coordinates is: {bbox}')
    bound_data = query_osm_results(bbox, qkey)
    data_dict = {element['id']: element for element in bound_data}
    counts = {element['id']: 1 for element in bound_data}

    num_of_coors_in_wkt = len(coordinates)
    if num_of_coors_in_wkt < samples:
        samples = num_of_coors_in_wkt
    last_index = num_of_coors_in_wkt - 1

    for _ in range(samples):
        # sample a bbox by sampling a coordinate from all set
        sample_bbox = create_bounding_box(coordinates, randint(0, last_index))
        sample_data = query_osm_results(sample_bbox, qkey)
        for element in sample_data:
            if element['id'] not in counts:
                counts[element['id']] = 0
            counts[element['id']] += 1

    ids = sorted(counts, key=counts.get, reverse=True)
    result = list()
    for identifier in ids:
        if identifier in data_dict:
            feature_type = data_dict[identifier]['type']
            feature_identifier = data_dict[identifier]['id']
            result.append({'type': feature_type,
                           'id': feature_identifier,
                           'tags': data_dict[identifier]['tags'],
                           'count': counts[identifier],
                           'lgd_uri': get_openstreetmap_member_uri(feature_type, feature_identifier)})
        # else:
        #     print(f'identifier {identifier} was not found in data_dict. skipped...')

    return result

# --- Helpers -----------------------------------------------------------------

def open_geom(fileName):
    ''' Open geometry file and read the WKT literals/coordinates '''

    lines = open(fileName, "r").readlines()
    geom_data = list()
    for line in lines:
        geom_dict = loads(line)
        geom_dict['wkt'] = parse_coordinates(geom_dict['wkt'])
        geom_data.append(geom_dict)
    return geom_data

def parse_coordinates(line):
    ''' Parse the WKT literals into coordinates '''

    coordinates = line.split(',')
    for i in range(len(coordinates)):
        coordinate = coordinates[i]
        coordinate = re_sub('[a-zA-Z"()]', '', coordinate)
        coordinate = coordinate.strip()
        coordinate = coordinate.split(' ')
        coordinate = {'lat': float(coordinate[1]), 'lng': float(coordinate[0])}
        coordinates[i] = coordinate
    return coordinates

def get_linkedgeodata_uris(segment, filter_key=''):
    ''' Get OSM instances info with their LinkedGeoData URIs '''

    lgd_uris = list()
    osm_lgd_data = get_openstreetmap_data(segment['wkt'], qkey=filter_key)
    for itm in osm_lgd_data:
        lgd_uris.append(itm['lgd_uri'])
    
    return lgd_uris

# --- entrypoint --------------------------------------------------------------

def main():

    ap = ArgumentParser(description='Process (jl) geometry file to acquire additional info from geo-coding services.\n\tUSAGE: python %s -g GEOMETRY_FILE -f FILTERING_KEY' % (basename(__file__)))
    ap.add_argument('-g', '--geometry_file', help='File (jl) holding the geometry info.', type=str)
    ap.add_argument('-f', '--filtering_key', help='String to filter OSM metadata by', default='', type=str)
    args = ap.parse_args()

    if args.geometry_file:
        segments = open_geom(args.geometry_file)
        print(f'there are {len(segments)} segments (collections of features/vectors) in input file')
        outfile = args.geometry_file.replace('.jl', '.lgd.jl')
        with open(outfile, 'w') as write_file:
            for seg in segments:
                print(f"generating LGD URIs for gid {seg['gid']} (has {len(seg['wkt'])} coordinate-tuples)")
                line_dict = OrderedDict()
                line_dict['gid'] = seg['gid']
                list_of_uris = get_linkedgeodata_uris(seg, args.filtering_key)
                print(f"found {len(list_of_uris)} LGD URIs for gid {seg['gid']}")
                line_dict['lgd_uris'] = list_of_uris
                write_file.write(dumps(line_dict) + '\n')
        print('Exported segments info to file %s' % (outfile))
    else:
        print('Input file was not provided.')
        exit(1)

if __name__ == '__main__':
    main()
