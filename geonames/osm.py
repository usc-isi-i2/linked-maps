import urllib
import json
import random
from parse_coordinates import openGeom,parseCoordinates
def getOSMData(coordinates = [{'lat':0,'lng':0}], service = 'findNearby'):    
    lat = [coord['lat'] for coord in coordinates]
    lng = [coord['lng'] for coord in coordinates]

    #http://overpass-api.de/api/interpreter?data=[out:json];way["railway"](41.5429254269,-122.000388261,41.7613897871,-121.688332858);out body;
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    query_key = '"railway"'
    query_box = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    query = "way[{key}]({s},{w},{n},{e});out body;".format(key=query_key,s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url = url_base + query
    response = urllib.urlopen(url)
    geoname_data = json.loads(response.read())
    return geoname_data

coordinates = (openGeom("geom.csv")[1])['wkt']
print ()
