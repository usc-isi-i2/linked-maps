import re
import os
import numpy as np
from osgeo.ogr import Open
from kneed import KneeLocator
import geopandas
import shapely


# def knee_detection(x, y, plot=False, **kwargs):
# 	assert len(y) == x
# 	kneedle = KneeLocator(range(x), y, **kwargs)
# 	if plot and kneedle.knee is not None:
# 		kneedle.plot_knee()
# 	return kneedle.knee


def get_map_files(folders):
	maps = []
	for folder in folders:
		all_files = [files for root, dirs, files in os.walk(folder)]
		shapefiles = [m for f in all_files for m in f if m.endswith('.shp')]
		maps.extend(shapefiles)
	return maps


def get_wkt_from_map(shapefile):
	shapefile = Open(shapefile)
	# print(shapefile.GetLayerCount())
	layer = shapefile.GetLayer(0)
	n_features = layer.GetFeatureCount()
	wkt = []
	for i in range(n_features):
		feature = layer.GetFeature(i)
		if feature and feature.GetGeometryRef():
			wkt.append(feature.GetGeometryRef().ExportToWkt())
	return wkt


def extract_from_segment(line):
	line = re.sub(r'[A-Z()]', '', line)
	coordinates = [c.strip() for c in line.split(',')]
	coordinates = [c.split() for c in coordinates]
	coordinates = [(float(c[0]), float(c[1])) for c in coordinates]
	return coordinates


def extract_geocoordinates(wkt, sort=False, unique=True):
	geocoordinates = []

	for line in wkt:
		coordinates = extract_from_segment(line)
		geocoordinates.extend(coordinates)

	if unique:
		geocoordinates = list(set(geocoordinates))
	if sort:
		geocoordinates.sort()

	return geocoordinates


def preprocess(shapefile, decimals=None):
	wkt = get_wkt_from_map(shapefile)
	geocoordinates = extract_geocoordinates(wkt)
	if decimals is not None:
		geocoordinates = np.array(geocoordinates).round(decimals)
	return geocoordinates


def get_cleaned_df(map_df, noise, decimals):
	''' Filter noisy segments and return only clean ones '''
	
	# Assuming that the shapefiles would have either all LINESTRING segs
	# or one MULTILINESTRING segment
	
	is_multiline = (len(map_df.geometry) == 1 and map_df.geometry[0].wkt.strip().startswith('MULTILINESTRING'))

	if is_multiline:
		mls = map_df.geometry[0].wkt.strip()
		coor_pairs = re.findall(r'\([-. \d]+,[-. \d]+\)', mls) # (-121.956231 41.587216, -121.956222 41.587041)
		
		clean_pairs = []

		for cpair in coor_pairs:
			cpair_ = cpair
			cpair = cpair.strip().replace('(', '').replace(')', '').split(',')
			cpair[0], cpair[1] = cpair[0].split(), cpair[1].split()
			cpair[0], cpair[1] = [float(c) for c in cpair[0]], [float(c) for c in cpair[1]]
			cpair[0], cpair[1] = np.array(cpair[0]).round(decimals).tolist(), np.array(cpair[1]).round(decimals).tolist()
			noisy = False
			for n in noise:
				if n in cpair:
					noisy = True
					break
			if not noisy:
				clean_pairs.append(cpair_)

		clean_mls = 'MULTILINESTRING ({})'.format(', '.join(clean_pairs))
		clean_mls = clean_mls.replace('\'', '')
 
		cleaned_df = geopandas.GeoDataFrame(map_df.to_dict())
		cleaned_df.geometry[0] = shapely.wkt.loads(clean_mls) # Assuming 'geometry' column has the wkt


	else:
		clean_segments = []
		for i, seg in enumerate(map_df.geometry):
			line = seg.wkt
			coordinates = extract_from_segment(line)
			coordinates = np.asarray(coordinates).round(decimals).tolist()

			noisy = False
			for coor in coordinates:
				if coor in noise:
					noisy = True
					break
			if not noisy:
				clean_segments.append(i)
		cleaned_df = geopandas.GeoDataFrame(map_df.geometry[clean_segments]).reset_index(drop=True)

	return cleaned_df
