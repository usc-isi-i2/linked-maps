import os
import argparse
import geopandas
import numpy as np
from agglomerative import AgglomerativeDenoiser
from dbscan import DBSCANDenoiser
from utils import extract_from_segment, get_cleaned_df


def denoise(shapefile, clustering=None, decimals=None, basis=None, explain=None, plot=None):
	# Filter Line Segments
	# Rewrite Shapefile
	print(shapefile)
	if clustering == 'agglomerative':
		denoiser = AgglomerativeDenoiser
	elif clustering == 'dbscan':
		denoiser = DBSCANDenoiser

	denoiser = denoiser(basis='representors', linkage='single', z=1)
	noise = denoiser.denoise(shapefile, decimals=decimals, basis=basis, explain=explain, plot=plot)
	print("Noise: ", len(noise))

	map_df = geopandas.read_file(shapefile)

	cleaned_df = get_cleaned_df(map_df, noise, decimals)
	cleaned_df.crs = {'init': 'epsg:4326'}

	filepath, ext = os.path.splitext(shapefile)
	outputfile = "{}_denoised{}".format(filepath, ext)

	cleaned_df.to_file(driver='ESRI Shapefile', filename=outputfile)

	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Denoise map shapefiles using clustering analysis')

	# parser.add_argument('--output', metavar='FILEPATH', type=str, nargs='?', help='default: <inputfile_denoised.shp>')
	parser.add_argument('--clustering', metavar='C', type=str, nargs='?', \
			help='agglomerative (default) or dbscan', default='agglomerative')
	parser.add_argument('--basis', metavar='B', type=str, nargs='?', \
			help='sorting basis: health (default) or density', default='health')
	parser.add_argument('--explain', metavar='%', type=float, nargs='?', help='percetage data to explain [0,1]')
	parser.add_argument('--plot', metavar='P', type=bool, nargs='?', help='Plot? Default: True', default=True)
	parser.add_argument('--decimals', metavar='D', type=int, nargs='?', help='Round D(6) places', default=6)
	parser.add_argument('shapefile', metavar='SHAPEFILE', type=str, nargs='+', help='input map shapefile')
	args = parser.parse_args()
	
	kwargs = {
		'clustering': args.clustering.lower(),
		'basis': args.basis,
		'explain': args.explain,
		'plot': args.plot,
		'decimals': args.decimals
	}
	
	for shapefile in args.shapefile:
		shapefile = os.path.realpath(shapefile)
		if not os.path.exists(shapefile) or not os.path.splitext(shapefile)[-1] == '.shp':
			print("Invalid shapefile", shapefile)
			continue

		denoise(shapefile, **kwargs)



