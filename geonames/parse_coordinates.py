import json
import re
def openGeom(fileName):
    lines = open(fileName,"r").readlines()
    geom_data = {}
    for line in lines:
        geom_dict = json.loads(line)
        geom_dict['wkt'] = parseCoordinates(geom_dict['wkt'])
        geom_data[geom_dict['gid']] = geom_dict
    return geom_data

def parseCoordinates(line):
    coordinates = line.split(',')
    for i in range(len(coordinates)):
        coordinate = coordinates[i]
        coordinate = re.sub('[a-zA-Z"()]', '', coordinate)
        coordinate = coordinate.strip()
        coordinate = coordinate.split(' ')
        coordinate = {'lat':float(coordinate[1]),'lng':float(coordinate[0])}
        coordinates[i] = coordinate
    return coordinates