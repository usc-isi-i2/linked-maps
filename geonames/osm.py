import urllib
import json
def getOSMData(coordinates = [{'lat':0,'lng':0}], key = '"route"="railway"', buffer = 0.01):    
    lat = [coord['lat'] for coord in coordinates]
    lng = [coord['lng'] for coord in coordinates]
	start_box = {'s':lat[0]-buffer,'n':lat[0]+buffer,'w':lng[0]-buffer,'e':lng[0]+buffer}
    end_box = {'s':lat[-1]-buffer,'n':lat[-1]+buffer,'w':lng[-1]-buffer,'e':lng[-1]+buffer}
	#http://overpass-api.de/api/interpreter?data=[out:json];way["railway"](41.5429254269,-122.000388261,41.7613897871,-121.688332858);out body;
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    query_key = key
    query_box = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    query = "relation[{key}]({s},{w},{n},{e});out body;".format(key=query_key,s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url = url_base + query
    response = urllib.urlopen(url)
    json_data = response.read()
    osm_data = json.loads(json_data)
    return osm_data['elements']

def printOSMData(osm_Data):
    for route in osm_Data:
        print (json.dumps(route['tags']))

