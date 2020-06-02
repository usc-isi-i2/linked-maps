import cv2
import os
import numpy as np
from matplotlib import pyplot as plt

TEMP_PATH = 'temp.png'

def create_image(data):
	''' Save the scatter plot (binarized) of data points to a png file '''
	fig = plt.figure()
	plt.scatter(data[:,0], data[:,1], color='red')
	plt.axis(False)
	fig.canvas.print_png(TEMP_PATH)
	plt.close()
	
	im = cv2.imread(TEMP_PATH)
	im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
	im = im[:, :, 1]
	im[im < 255] = 0
	im = np.abs(im - 255)
	return im, fig

def delete_image():
	path = os.path.join(os.getcwd(), TEMP_PATH)
	if os.path.exists(TEMP_PATH):
		os.remove(path)
