import urllib
import json
import random
from parse_coordinates import openGeom,parseCoordinates
geonames_service = {
    'findNearby':"http://api.geonames.org/findNearbyJSON?",
    'findNearbyPlaceName':"http://api.geonames.org/findNearbyPlaceNameJSON?",
    'findNearbyWikipedia':"http://api.geonames.org/findNearbyWikipediaJSON?"
    }
def generateRandomCoordinate(north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinate = {'lat':random.uniform(north,south),'lng':random.uniform(west,east)}
    return coordinate

def generateRandomCoordinates(N=10,north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinates = [ generateRandomCoordinate(north,south,east,west) for _ in range(N)]
    return coordinates
    
def getGeonameData(coordinate = {'lat':0,'lng':0}, service = 'findNearby'):    
    username = "jainvasu631"
    # http://api.geonames.org/findNearbyJSON?lat=47.3&lng=19&username=jainvasu631
    url_base = geonames_service['findNearbyWikipedia']
    url_params = "lat="+str(coordinate['lat'])+"&lng="+str(coordinate['lng'])+"&username="+username
    url = url_base + url_params
    response = urllib.urlopen(url)
    geoname_data = json.loads(response.read())
    return geoname_data

def getGeonamesData(coordinates,service = 'findNearby' ):
    geoname_data = [getGeonameData(coordinate,service) for coordinate in coordinates]
    return geoname_data

segment1 = openGeom("geom.csv")[1]
print segment1
print len(segment1['wkt'])
#print getGeonamesData(segment1['wkt'])