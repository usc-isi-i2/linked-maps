import random
import urllib
import json

def queryResult(query_box = {'s':0,'n':0,'w':0,'e':0}, query_key = ""):
    #http://overpass-api.de/api/interpreter?data=[out:json];way["railway"](41.5429254269,-122.000388261,41.7613897871,-121.688332858);out body;
    if query_key:
        query_key = "[{key}]".format(key=query_key)
    query = "relation{key}({s},{w},{n},{e});out body;".format(key=query_key,s=query_box['s'],n=query_box['n'],w=query_box['w'],e=query_box['e'])
    url_base = "http://overpass-api.de/api/interpreter?data=[out:json];"
    url = url_base + query
    response = urllib.urlopen(url)
    try:
        json_data = response.read()
        osm_data = json.loads(json_data)
        return osm_data['elements']
    except ValueError as _:
        print(query_box)
        print("ValueError")
        return []

def createBBox(coordinates = [{'lat':0,'lng':0}],index = None,buffer = 0.001):
    if index is None:
        lat = [coord['lat'] for coord in coordinates]
        lng = [coord['lng'] for coord in coordinates]
        bbox = {'s':min(lat),'n':max(lat),'w':min(lng),'e':max(lng)}
    else:
        lat = coordinates[index]['lat']
        lng = coordinates[index]['lng']
        bbox = {'s':lat-buffer,'n':lat+buffer,'w':lng-buffer,'e':lng + buffer}
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

def getOSMData(coordinates = [{'lat':0,'lng':0}], key = '', samples = 10):
    last_index = len(coordinates) -1
    bbox = createBBox(coordinates,None)
    print bbox
    bound_data = queryResult(bbox,key)
    data_dict = {element['id']:element for element in bound_data}
    counts = {element['id']:0 for element in bound_data}
    for _ in range(samples):
        sample_bbox = createBBox(coordinates, random.randint(0,last_index))
        sample_data = queryResult(sample_bbox,key)
        for element in sample_data:
            counts[element['id']]+=1
    ids = sorted(counts, key=counts.get, reverse=True)
    for id in ids:
        data_dict[id]['count'] = counts[id]
        del data_dict[id]['members']
    result = [data_dict[id] for id in ids]
    return result

def printOSMData(osm_data):
    for route in osm_data:
        print(json.dumps(route))

