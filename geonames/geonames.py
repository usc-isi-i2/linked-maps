import urllib
import json
import random
geonames_service = {
    'findNearby':"http://api.geonames.org/findNearbyJSON?",
    'findNearbyPlaceName':"http://api.geonames.org/findNearbyPlaceNameJSON?",
    'findNearbyWikipedia':"http://api.geonames.org/findNearbyWikipediaJSON?"
    }
location_ref = {}
for i in range(1):
    lat = str(random.uniform(32,42))
    lng = str(random.uniform(-124,-117))
    coordinates = (lat,lng)
    username = "jainvasu631"
    # http://api.geonames.org/findNearbyJSON?lat=47.3&lng=19&username=jainvasu631
    url_base = geonames_service['findNearbyWikipedia']
    url_params = "lat="+lat+"&lng="+lng+"&username="+username
    url = url_base + url_params
    response = urllib.urlopen(url)
    result = json.loads(response.read())
    location_ref[coordinates] = result
print location_ref