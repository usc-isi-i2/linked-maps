import torch
import torchvision.transforms.functional as TF
import matplotlib.pyplot as plt
import os
import cv2
from losses import dice_coeff


def load_images(m_paths, grayscale=False):
	''' read as images using OpenCV '''
	images = []
	for mp in m_paths:
		im = cv2.imread(mp)
		if grayscale:
			im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
		else:
			im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
		images.append(im)
	return images

'''
def dice_coeff(pred, target):
	eps = 0.0001
	assert pred.shape[-2:] == target.shape[-2:]

	if pred.is_cuda:
		coeff = torch.FloatTensor(1).cuda().zero_()
	else:
		coeff = torch.FloatTensor(1).zero_()
	
	for i, (p, t) in enumerate(zip(pred, target)):
		p, t = p.view(-1), t.view(-1)
		numerator = (2 * torch.dot(p, t)).float()
		denominator = (p.sum() + t.sum()).float() + eps
		coeff += (numerator / denominator)

	return coeff / (i + 1)
'''

def get_filepaths(data_dir, pos_class, neg_classes):
	''' requires the map images to start with 'map_' and
		corresponding masks to start with 'mask_'
	'''

	maps, masks = [], []
	# pos_file = [] # using mask to determine the positive pixels/coors
	neg_files = []

	for map_dir in os.listdir(data_dir):
		if map_dir.startswith('.'):
			continue
		_, _, files = list(os.walk(os.path.join(data_dir, map_dir)))[0]
		n = []
		for f in files:
			filepath = os.path.join(data_dir, map_dir, f)    
			
			if f.startswith('map_'):
				maps.append(filepath)
				
			elif f.startswith('mask_'):
				masks.append(filepath)
				
			else:
				for neg in neg_classes:
					if neg in f.lower() and pos_class not in f.lower() and f.endswith('.txt'):
						n.append(filepath)
		neg_files.append(n)
	return maps, masks, neg_files


def plot_overlay(image, mask):
	''' overlay a mask over the image '''

#	if image.__class__.__name__ == 'Tensor':
#		image = image.numpy().transpose((1,2,0))
#		mask = mask.numpy().transpose((1,2,0)).squeeze()
	
	plt.figure()
	plt.imshow(image)
	plt.imshow(mask, cmap='gray', alpha=0.55)
	plt.show()


def write_sample_points(samples, filename):
	''' write sampled pixels coordinates to files (eg. pos.txt, neg1.txt) '''
	with open(filename, 'w') as f:
		output = [("%d,%d" % (s[0],s[1])) for s in samples]
		output = '\n'.join(output)
		f.write(output)


def make_batch(image, win_size, stride, batch_size, start_row=0, start_col=0):
	''' make a batch generator for patches of win_size from image '''
	batch, coords = [], []
	for row in range(start_row, image.shape[0]-win_size, stride):
		for col in range(start_col, image.shape[1]-win_size, stride):
			s_y, e_y = row, row + win_size
			s_x, e_x = col, col + win_size
			patch = image[s_y:e_y, s_x:e_x]
			patch = TF.to_pil_image(patch)
			patch = TF.to_tensor(patch)
			patch = patch.unsqueeze(0) # add batch dim
			batch.append(patch)
			coords.append(((s_y, e_y), (s_x, e_x)))
			
			if len(batch) == batch_size:
				yield (torch.cat(batch, dim=0), coords)
				batch.clear()
				coords.clear()
			elif (e_y+stride >= image.shape[0]) and (e_x+stride >= image.shape[1]) and len(batch):
				yield (torch.cat(batch, dim=0), coords) # batch of the last remaining patches


def plot_segmentation_row(**kwargs):
	plt.figure(figsize=(16,5))

	for i, (name, image) in enumerate(kwargs.items(), 1):
		plt.subplot(1, len(kwargs), i)
		plt.xticks([])
		plt.yticks([])
		plt.title(' '.join(name.split('_')).title())
		plt.imshow(image)
