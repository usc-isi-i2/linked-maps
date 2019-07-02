import json
import random
from parse_coordinates import openGeom,parseCoordinates
from geonames import getGeonameData,getGeonamesData
from osm import getOSMData
def generateRandomCoordinate(north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinate = {'lat':random.uniform(north,south),'lng':random.uniform(west,east)}
    return coordinate

def generateRandomCoordinates(N=10,north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinates = [ generateRandomCoordinate(north,south,east,west) for _ in range(N)]
    return coordinates
    

segment1 = openGeom("geom.csv")[1]
print segment1
print len(segment1['wkt'])
#print getGeonamesData(segment1['wkt'])

segments = openGeom("geom.csv")
railroad_tags = []
railroad_names = {}
print(len(segments))
for segment in segments:
	coordinates = segments[segment]['wkt']
	osm_data = getOSMData(coordinates)
	for element in osm_data:
		route = element['tags']
		if route['name'] in railroad_names:
			railroad_names[route['name']] += 1
		else:
			railroad_tags.append(route)
			railroad_names[route['name']] = 1
print(railroad_names) 
print(railroad_tags)