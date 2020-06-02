import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
import matplotlib.pyplot as plt
import os
import cv2
from collections import namedtuple
from utils import load_images, write_sample_points

try:
	from pyclustering.cluster import cure
except ImportError:
	pass


DataPoint = namedtuple('CenterPixel', 'map_id coord label')
AugmentedDataPoint = namedtuple('CenterPixel', 'map_id coord label hflip vflip angle')


class SegmentationDataset(Dataset):
	def __init__(self, data_points, transformer, win_size, scale=False):
		self.dataset = data_points
		self.transformer = transformer
		self.win_size = win_size
		self.scale = scale
		
	def preprocess(self, data_point):
		data_point = self.transformer(data_point)
		# mask channels == n_classes?
		
#         data_point['image'] = data_point['mask'].to(torch.float64)
#         data_point['mask'] = data_point['mask'].to(torch.long)
#         if self.scale: # totensor transform has done that for us
#             data_point['image'] /= 255.
#             data_point['mask'] /= 255
		return data_point
		
	def __len__(self):
		return len(self.dataset)
	
	def __getitem__(self, ix):
		assert ix < self.__len__(), 'Index must be within bounds (<len)'
		return self.preprocess(self.dataset[ix])


def get_data(maps, loaded_images, n_aug_pos, n_aug_neg, win_size, rotation_range,
			val_size=0.1, shuffle=True, augment=True):
	''' returns training and validation data '''

	data = collate_data(maps, loaded_images, n_aug_pos, n_aug_neg, win_size, rotation_range,
						shuffle=shuffle, augment=augment)

	n_val = int(len(data) * val_size)
	n_train = len(data) - n_val
	train_data, val_data = random_split(data, [n_train, n_val])
	return train_data, val_data


def collate_data(maps, loaded_images, n_aug_pos, n_aug_neg, win_size, rotation_range, augment=True, shuffle=False): 
	dataset = []
	
	for m_ix, map_ in enumerate(maps):
		map_path, map_name = os.path.split(map_)
		_, _, files = list(os.walk(map_path))[0]
		
		for f in files:
			filepath = os.path.join(map_path, f)

			if not f.endswith('.txt'):
				continue
			if not f.startswith('pos') and not f.startswith('neg'):
				continue
			
			coords = np.loadtxt(filepath, dtype=int, delimiter=',', ndmin=2)
			label = 'p' if f.startswith('pos') else 'n'
			n_aug = (n_aug_pos if label == 'p' else n_aug_neg)
			
			for coord in coords:
				point = DataPoint(m_ix, coord, label)
				if not is_valid_pixel(point, *loaded_images[point.map_id].shape[:2], win_size):
					continue
				
				if augment:
					aug_point = AugmentedDataPoint(*point, hflip=False, vflip=False, angle=0)
					dataset.append(aug_point) # Original
					
					for _ in range(n_aug):
						aug_point = AugmentedDataPoint(*point, **get_augmented_params(rotation_range))
						dataset.append(aug_point)
				else:
					dataset.append(point)
								
	if shuffle:
		np.random.shuffle(dataset)
	return dataset


def get_augmented_params(rotation_range=None):
	hflip, vflip, theta = False, False, 0
	if np.random.random() < 0.5:
		hflip = True
	if np.random.random() < 0.5:
		vflip = True
	if rotation_range is not None:
		theta = int(np.random.uniform(-rotation_range, rotation_range))
	return {'hflip': hflip, 'vflip': vflip, 'angle': theta}


def is_valid_pixel(data_point, rows, cols, win_size):
	''' check if pixel coords are within image size '''
	# rows, cols = loaded_maps[data_point.map_id].shape[:2]
	center_pixel = data_point.coord
	start_y = int(center_pixel[0] - (win_size - 1)/2)
	start_x = int(center_pixel[1] - (win_size - 1)/2)
	end_y = start_y + win_size
	end_x = start_x + win_size 
	if start_y >= 0 and start_x >= 0 and end_y < rows and end_x < cols:
		return True
	return False
	

def sample_points(maps, masks, neg_files, n_pos, n_neg, representors=False, plot_pos=False):
	''' Sample `n` points/pixels from image to generate training data from and write to files '''
	
	for m, mask, negf in zip(maps, masks, neg_files):
		filepath = os.path.split(m)[0]
		
		mask = cv2.imread(mask)
		mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

		pos_pixels = np.argwhere(mask==255) # pixels corresponding to positive class
#         print(pos_pixels.shape)
#         print(pos_pixels)

		if representors:
			# great, but takes forever just for 1 map :/
			representors = cure.cure(pos_pixels, number_cluster=1, number_represent_points=n_pos, compression=0)
			representors = representors.process().get_representors()
			pos_samples = np.asarray(representors[0], dtype=int)
		else: # sample randomly
			pos_samples = np.random.choice(len(pos_pixels), n_pos, replace=False)
			pos_samples = pos_pixels[pos_samples]
		write_sample_points(pos_samples, os.path.join(filepath, 'pos.txt'))
		
		if plot_pos:
			plt.figure()
			plt.scatter(pos_pixels[:,0], pos_pixels[:,1])
			plt.scatter(pos_samples[:,0], pos_samples[:,1], marker='*', color='yellow', s=1.5)
			plt.show()
		
		for i, neg in enumerate(negf, 1):
			neg_pixels = np.loadtxt(neg, dtype=int, delimiter=',', ndmin=2)
			neg_samples = np.random.choice(len(neg_pixels), n_neg, replace=False)
			neg_samples = neg_pixels[neg_samples]
			write_sample_points(neg_samples, os.path.join(filepath, 'neg%d.txt' % i))
			
			