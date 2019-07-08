import urllib
import json

def queryResult(query_box = {'s':0,'n':0,'w':0,'e':0}, query_key = 'route'):
    #http://overpass-api.de/api/interpreter?data=[out:json];way["railway"](41.5429254269,-122.000388261,41.7613897871,-121.688332858);out body;
    query = "relation[{key}]({s},{w},{n},{e});out body;".format(key=query_key,s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    url = url_base + query
    response = urllib.urlopen(url)
    try:
        json_data = response.read()
        osm_data = json.loads(json_data)
        return osm_data['elements']
    except ValueError as _:
        print("ValueError")
        return {}

def createBBox(coordinates = [{'lat':0,'lng':0}], buffer = 0.0001):
    lat = [coord['lat'] for coord in coordinates]
    lng = [coord['lng'] for coord in coordinates]
    bbox = {}
    bbox['start'] = {'s':lat[0]-buffer,'n':lat[0]+buffer,'w':lng[0]-buffer,'e':lng[0]+buffer}
    bbox['end'] = {'s':lat[-1]-buffer,'n':lat[-1]+buffer,'w':lng[-1]-buffer,'e':lng[-1]+buffer}
    bbox['bound'] = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    return bbox

def unionOSM(osm_data = []):
    if len(osm_data):
        union = {}
        for osm_elements in osm_data:
            for datum in osm_elements:
                id = datum['id']
                if id not in union:
                    union[id] = datum
        return union
    else:
        return {}

def intersectionOSM(osm_data = []):
    if len(osm_data):
        intersection = {datum['id']:datum for datum in osm_data[0]}
        for osm_elements in osm_data:
            ids = {datum['id']:datum for datum in osm_elements}
            new_intersection = {}
            for id in intersection:
                if id in ids:
                    new_intersection[id] = intersection[id]
            intersection = new_intersection
        return intersection
    else:
        return {}

def getOSMData(coordinates = [{'lat':0,'lng':0}], key = '"route"="railway"', method = 'bound'):
    bbox = createBBox(coordinates)
    start_data = queryResult(bbox['start'],key)
    print bbox['start']
    print bbox['end']
    end_data = queryResult(bbox['end'],key)
    #bound_data = queryResult(bbox['bound'],key)
    return unionOSM([start_data,end_data])
    #return queryResult(bbox['bound'],key)

def printOSMData(osm_data):
    for route in osm_data.values():
        print (json.dumps(route['tags']))

