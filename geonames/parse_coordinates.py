
def openCoordinates(fileName):
    lines = open(fileName,"r").readlines()
    coordinate_data = []
    for line in lines:
        coordinate_data.append(parseCoordinates(line))
    return coordinate_data

def parseCoordinates(line):
    coordinates = line.split(',')
    for coordinate in coordinates:
        coordinate = coordinate.translate(None,'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"(,)')
        coordinate = coordinate.strip()
        coordinate = coordinate.split(' ')
    return coordinates