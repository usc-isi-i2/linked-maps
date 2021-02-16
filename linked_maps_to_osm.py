# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import OrderedDict
from json import loads, dumps
from os.path import basename
from random import uniform, choice
from time import time, sleep
from re import sub as re_sub
from requests import get as get_request
from shapely import wkt
from shapely.geometry import Point

MAX_POLYGON_SAMPLE_RETRIES = 20


# --- OSM API -----------------------------------------------------------------

def get_openstreetmap_member_uri(osm_type, osm_id):
    ''' Get OSM URI '''

    return "https://www.openstreetmap.org/" + str(osm_type) + "/" + str(osm_id)


def query_osm_results(query_box={'s': 0, 'n': 0, 'w': 0, 'e': 0}, filter_tag_or_tagval=''):
    ''' Query OSM 'relation' data elements in a given bounding box.
    'relation' elements are used to organize multiple nodes or ways into a larger whole.
    
    Generates an OSM http request and return response in JSON format.
    i.e. 
    http://overpass-api.de/api/interpreter?data=[out:json];node(41.5,-122.0,41.7,-121.6);%3C;out%20meta; '''

    query = "node({s},{w},{n},{e});<;out meta;".format(s=query_box['s'], n=query_box['n'],
                                                       w=query_box['w'], e=query_box['e'])
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    ''' This call includes:
        - all nodes in the bounding box,
        - all ways that have such a node as member,
        - and all relations that have such a node or such a way as members. '''
    url = url_base + query
    try:
        sleep(0.5)
        req_start_time = time()
        osm_data = get_request(url).json()
        print('   Request took %.2f seconds' % (time() - req_start_time))
        if filter_tag_or_tagval != '':
            filtered_set = list()
            for itm in osm_data['elements']:
                if 'tags' in itm:
                    if filter_tag_or_tagval in itm['tags']:
                        filtered_set.append(itm)
                    else:
                        for itag in itm['tags']:
                            if itm['tags'][itag] == filter_tag_or_tagval:
                                filtered_set.append(itm)
            return filtered_set
        return osm_data['elements']
    except ValueError as e:
        print('ValueError for query_box' + str(query_box) + " | " + str(e))
        return []


def create_bounding_box__multiline(coordinates, random=False, buffer=0.001):
    ''' Create a bounding box given a set of latitude and longitude coordinates. '''

    if not random:
        lat = [coord['lat'] for coord in coordinates]
        lng = [coord['lng'] for coord in coordinates]
        bbox = {'s': min(lat), 'n': max(lat), 'w': min(lng), 'e': max(lng)}
    else:
        random_choice = choice(coordinates)
        lat = random_choice['lat']
        lng = random_choice['lng']
        bbox = {'s': lat-buffer, 'n': lat+buffer, 'w': lng-buffer, 'e': lng+buffer}
    return bbox


def get_random_point_in_polygon(poly):
    ''' Get random point in Polygon '''
    minx, miny, maxx, maxy = poly.bounds
    esc_counter = 0
    while True:
        p = Point(uniform(minx, maxx), uniform(miny, maxy))
        esc_counter += 1
        if poly.contains(p):
            return p
        if esc_counter > MAX_POLYGON_SAMPLE_RETRIES:
            return poly.representative_point()


def create_bounding_box__multipolygon(coordinates, random=False, buffer=0.001):
    ''' Create a bounding box given a MULTIPOLYGON shapely object. '''

    full_poly = wkt.loads(coordinates)
    if not random:
        minx, miny, maxx, maxy = full_poly.bounds
        bbox = {'s': miny, 'n': maxy, 'w': minx, 'e': maxx}
    else:
        # chose one polygon randomly
        random_poly = choice(list(full_poly))
        try:
            random_choice = get_random_point_in_polygon(random_poly)
        except Exception as e:
            print("exception in create_bounding_box__multipolygon: " + str(e))
            random_choice = random_poly.representative_point()
            pass
        lat = random_choice.y
        lng = random_choice.x
        bbox = {'s': lat-buffer, 'n': lat+buffer, 'w': lng-buffer, 'e': lng+buffer}
    return bbox


def get_openstreetmap_data(coordinates, qkey='', samples=10):
    ''' Get OSM data and metadata '''

    is_poly = False
    # get bbox that contains all of the coordinates
    if 'POLYGON' in coordinates:
        is_poly = True
        bbox = create_bounding_box__multipolygon(coordinates)
    else:
        bbox = create_bounding_box__multiline(coordinates)

    bound_data = query_osm_results(bbox, qkey)
    data_dict = {element['id']: element for element in bound_data}
    counts = {element['id']: 1 for element in bound_data}

    for _ in range(samples):
        # sample a bbox by sampling a coordinate from all set
        if is_poly:
            sample_bbox = create_bounding_box__multipolygon(coordinates, random=True)
        else:
            sample_bbox = create_bounding_box__multiline(coordinates, random=True)
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
            osm_uri = get_openstreetmap_member_uri(feature_type, feature_identifier)
            result.append({'type': feature_type,
                           'id': feature_identifier,
                           'tags': data_dict[identifier]['tags'],
                           'count': counts[identifier],
                           'osm_uri': osm_uri})

    return result


# --- Helpers -----------------------------------------------------------------

def open_geom(fileName):
    ''' Open geometry file and read the WKT literals/coordinates '''

    lines = open(fileName, "r").readlines()
    geom_data = list()
    for line in lines:
        geom_dict = loads(line)
        if 'POLYGON' not in geom_dict['wkt']:  # special parsing for line data (backward compatibility)
            geom_dict['wkt'] = parse_multiline_coordinates(geom_dict['wkt'])
        geom_data.append(geom_dict)
    return geom_data


def parse_multiline_coordinates(line):
    ''' Parse the WKT literals into coordinates (multi-line case) '''

    coordinates = line.split(',')
    for i in range(len(coordinates)):
        coordinate = coordinates[i]
        coordinate = re_sub('[a-zA-Z"()]', '', coordinate)
        coordinate = coordinate.strip()
        coordinate = coordinate.split(' ')
        coordinate = {'lat': float(coordinate[1]), 'lng': float(coordinate[0])}
        coordinates[i] = coordinate
    return coordinates


def get_osm_uris(segment, filter_key=''):
    ''' Get OSM instances info with their LinkedGeoData URIs '''

    osm_uris = list()
    osm_data = get_openstreetmap_data(segment['wkt'], qkey=filter_key)
    for itm in osm_data:
        print('osm_uri=%s, counts=%d' % (itm["osm_uri"], itm["count"]))
        if itm["count"] > 1:  # remove this statement for baseline results
            osm_uris.append(itm['osm_uri'])
    
    return osm_uris


# --- entrypoint --------------------------------------------------------------

def main():

    ap = ArgumentParser(description='Process (jl) geometry file to acquire additional info from geo-coding services.\n\tUSAGE: python %s -g GEOMETRY_FILE -f FILTERING_KEY' % (basename(__file__)))
    ap.add_argument('-g', '--geometry_file', help='File (jl) holding the geometry info.', type=str)
    ap.add_argument('-f', '--filtering_key', help='String to filter OSM metadata by', default='railway', type=str)
    args = ap.parse_args()

    if args.geometry_file:
        segments = open_geom(args.geometry_file)
        print('there are %d segments (collections of features/vectors) in input file' % (len(segments)))
        outfile = args.geometry_file.replace('.jl', '.osm.jl')
        with open(outfile, 'w') as write_file:
            for seg in segments:
                if 'POLYGON' in seg['wkt']:
                    tot_coor_tuples = 0
                    for polygon in list(wkt.loads(seg['wkt'])):
                        tot_coor_tuples += len(polygon.exterior.coords)
                else:
                    tot_coor_tuples = len(seg['wkt'])
                print("generating OSM URIs for gid %s (has %d coordinate-tuples)" % (str(seg['gid']), tot_coor_tuples))
                line_dict = OrderedDict()
                line_dict['gid'] = seg['gid']
                list_of_uris = get_osm_uris(seg, args.filtering_key)
                print("found %d OSM URIs for gid %s" % (len(list_of_uris), str(seg['gid'])))
                line_dict['osm_uris'] = list_of_uris
                write_file.write(dumps(line_dict) + '\n')
        print('Exported segments info to file %s' % (outfile))
    else:
        print('Input file was not provided.')
        exit(1)


if __name__ == '__main__':
    main()
