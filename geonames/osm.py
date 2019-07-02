import urllib
import json

def queryResult(query_box = {'s':0,'n':0,'w':0,'e':0}, query_key = 'route'):
    #http://overpass-api.de/api/interpreter?data=[out:json];way["railway"](41.5429254269,-122.000388261,41.7613897871,-121.688332858);out body;
    query = "relation[{key}]({s},{w},{n},{e});out body;".format(key=query_key,s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    url = url_base + query
    response = urllib.urlopen(url)
    json_data = response.read()
    osm_data = json.loads(json_data)
    return osm_data['elements']

def createBBox(coordinates = [{'lat':0,'lng':0}], buffer = 0.01):
    lat = [coord['lat'] for coord in coordinates]
    lng = [coord['lng'] for coord in coordinates]
    bbox = {}
    bbox['start'] = {'s':lat[0]-buffer,'n':lat[0]+buffer,'w':lng[0]-buffer,'e':lng[0]+buffer}
    bbox['end'] = {'s':lat[-1]-buffer,'n':lat[-1]+buffer,'w':lng[-1]-buffer,'e':lng[-1]+buffer}
    bbox['bound'] = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    return bbox
    
def getOSMData(coordinates = [{'lat':0,'lng':0}], key = '"route"="railway"', method = 'bound'):
    bbox = createBBox(coordinates)
    #start_data = queryResult(bbox['start'],key)
    #end_data = queryResult(bbox['end'],key)
    #bound_data = queryResult(bbox['bound'],key)
    return queryResult(bbox['bound'],key)

def printOSMData(osm_Data):
    for route in osm_Data:
        print (json.dumps(route['tags']))

