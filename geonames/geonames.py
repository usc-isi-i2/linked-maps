import urllib
import json
import random
from parse_coordinates import openCoordinates,parseCoordinates
geonames_service = {
    'findNearby':"http://api.geonames.org/findNearbyJSON?",
    'findNearbyPlaceName':"http://api.geonames.org/findNearbyPlaceNameJSON?",
    'findNearbyWikipedia':"http://api.geonames.org/findNearbyWikipediaJSON?"
    }
coordinates = openCoordinates("coordinates")
def generateRandomCoordinates(north=90,south=-90,east=180,west=-180, N=10):
    coordinates = [{'lat':random.uniform(north,south),'lng':random.uniform(west,east)} for i in range(N)]
    return coordinates
    
def getGeonameData(coordinate = {'lat':0,'lng':0}, service = 'findNearby'):    
    username = "jainvasu631"
    # http://api.geonames.org/findNearbyJSON?lat=47.3&lng=19&username=jainvasu631
    url_base = geonames_service['findNearbyWikipedia']
    url_params = "lat="+coordinate['lat']+"&lng="+coordinate['lng']+"&username="+username
    url = url_base + url_params
    response = urllib.urlopen(url)
    geoname_data = json.loads(response.read())
    return geoname_data

def getGeonamesData(coordinates,service = 'findNearby' ):
    geoname_data = [getGeonameData(coordinate,service) for coordinate in coordinates]
    return geoname_data