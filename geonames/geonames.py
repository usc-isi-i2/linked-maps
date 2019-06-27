import urllib
import json
(lat,lng) = ('0','0')
username = "jainvasu631"
# http://api.geonames.org/findNearbyJSON?lat=47.3&lng=19&username=jainvasu631
url_base = "http://api.geonames.org/findNearbyJSON?"
url_params = "lat="+lat+"&lng="+lng+"&username="+username
url = url_base + url_params
print(url)
response = urllib.urlopen(url)
result = json.loads(response.read())
print(result) 