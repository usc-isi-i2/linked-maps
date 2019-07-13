import json
import random
from parse_coordinates import openGeom,parseCoordinates
from geonames import getGeonameData,getGeonamesData
from osm import getOSMData,printOSMData,addURIs

def generateRandomCoordinate(north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinate = {'lat':random.uniform(north,south),'lng':random.uniform(west,east)}
    return coordinate

def generateRandomCoordinates(N=10,north=90.0,south=-90.0,east=180.0,west=-180.0):
    coordinates = [ generateRandomCoordinate(north,south,east,west) for _ in range(N)]
    return coordinates
        
def testGeonames(segment):
    print getGeonameData(segment['wkt'][1])

def testOSM(segment):
    printOSMData(addURIs(getOSMData(segment['wkt'])))

def testSegment(segment):
    print segment['gid']
    print len(segment['wkt'])
    #testGeonames(segment)
    testOSM(segment)

segments = openGeom("csv7/geom.csv")
print len(segments.keys())
testSegment(segments[1])
