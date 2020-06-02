import os
import sys
import tifffile
import numpy as np
import matplotlib.pyplot as plt
from osgeo.ogr import Open
from utils import preprocess

BLACK = 0
WHITE = 1
TEMP_IM = 'temp_im.tif'
TEMP_GT = 'temp_gt.tif'

def evaluate(im, gt, buffer=0):
	print("  Line Width:", 2*buffer+1)
	im = im.astype('int')
	im[im != BLACK] = WHITE

	gt = gt.astype('int')
	gt[gt != BLACK] = WHITE

	# Add Buffer to GT
	gt = gt.flatten()
	indices = np.where(gt == WHITE)[0]
	
	to_the_left, to_the_right = list(), list()
	
	while buffer:
		to_the_left.extend((indices-buffer).tolist())
		to_the_right.extend((indices+buffer).tolist())
		buffer -= 1
	
	to_the_left, to_the_right = np.asarray(to_the_left), np.asarray(to_the_right)
	to_the_left, to_the_right = to_the_left[to_the_left>=0], to_the_right[to_the_right<gt.shape[0]]
	to_the_left, to_the_right = np.unique(to_the_left), np.unique(to_the_right)
	
	if any(to_the_left):
		gt[to_the_left] = WHITE
	if any(to_the_right):
		gt[to_the_right] = WHITE
	
	gt = gt.reshape(im.shape)
	
	# print(im.shape, gt.shape)
	# print(im.sum(), gt.sum())

	tp = np.logical_and(im, gt).sum() # in both
	fp = ((im - gt) == WHITE).sum() # only in im
	fn = ((gt - im) == WHITE).sum() # only in gt
	# print(tp, fp, fn)

	iou_score = tp/(tp+fp+fn)
	precision = tp/(tp+fp)
	recall    = tp/(tp+fn)
	f1_score  = 2 * ( (precision * recall) / (precision + recall) )

	print("    F1:", round(f1_score, 4))
	print("    Correctness (P):", round(precision, 4))
	print("    Completeness(R):", round(recall, 4))
	print("    IoU:", round(iou_score, 4))

	# plt.figure()
	# plt.imshow(im, cmap='gray')
	# plt.show()

	# plt.figure()
	# plt.imshow(gt, cmap='gray')
	# plt.show()


def rasterize(im, gt, decimals=6, res=(1000,1000), delta=0.01):
	# im_layer = Open(im).GetLayer().GetName()
	# gt_layer = Open(gt).GetLayer().GetName()
	im_layer = im.split('/')[-1].split('.')[0]
	gt_layer = gt.split('/')[-1].split('.')[0]

	im_coors = preprocess(im, decimals=decimals)
	gt_coors = preprocess(gt, decimals=decimals)

	xmin = min(im_coors[:, 0].min(), gt_coors[:, 0].min()) - delta
	xmax = max(im_coors[:, 0].max(), gt_coors[:, 0].max()) + delta
	ymin = min(im_coors[:, 1].min(), gt_coors[:, 1].min()) - delta
	ymax = max(im_coors[:, 1].max(), gt_coors[:, 1].max()) + delta

	# GDAL_RASTERIZE = "gdal_rasterize -l {} -a FID -ts {} {} -q -a_nodata 0.0 -te {} {} {} {} -ot Float32 -of GTiff {} {}"
	GDAL_RASTERIZE = "gdal_rasterize -l {} -burn 255 -ts {} {} -q -a_nodata 0.0 -te {} {} {} {} -ot Float32 -of GTiff {} {}"
	rasterize_im = GDAL_RASTERIZE.format(im_layer, res[0], res[1], xmin, ymin, xmax, ymax, im, TEMP_IM)
	rasterize_gt = GDAL_RASTERIZE.format(gt_layer, res[0], res[1], xmin, ymin, xmax, ymax, gt, TEMP_GT)

	os.system(rasterize_im)
	os.system(rasterize_gt)



if __name__ == '__main__':
	# arg1: extracted    arg2: groundtruth
	im, gt = sys.argv[1], sys.argv[2] # shapefiles

	# decimals = 6 if len(sys.argv) > 3 int(sys.argv[3])

	resolutions = [(100,100), (508,508), (600,600), (1000,1000)]
	buffers = [0, 1, 2]

	for res in resolutions:
		print("---- {} X {} ----".format(res[0], res[1]))
		rasterize(im, gt, res=res)

		im_tiff = tifffile.imread(TEMP_IM)
		gt_tiff = tifffile.imread(TEMP_GT)

		for buffer in buffers:
			evaluate(im_tiff, gt_tiff, buffer=buffer)
		
	# os.remove(TEMP_IM)
	# os.remove(TEMP_GT)
	
