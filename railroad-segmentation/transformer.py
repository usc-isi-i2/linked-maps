import torch
import torchvision.transforms.functional as TF
import numpy as np

class SegmentationTransform:
	''' Returns cropped map image and mask (augmented) for a data point '''
	
	def __init__(self, loaded_images, loaded_masks, win_size, image_tf=None, mask_tf=None, normalizer=None, make_one_hot=False):
		self.data_point = None
		self.loaded_images = loaded_images
		self.loaded_masks = loaded_masks
		self.win_size = win_size
		self.image_tf = image_tf # Additional transforms to be applied to the PIL Image
		self.mask_tf = mask_tf
		self.normalizer = normalizer # Normalize the mean, std of the tensor
		self.make_one_hot = make_one_hot # Convert mask to CxHxW
		
	def _compute_patch_start_coords(self, image, data_point):
		# TF.crop pads the image if out of bounds;
		# but `is_valid` made sure it is within bounds
		rows, cols = image.shape[:2]
		center_pixel = data_point.coord
		start_y = int(center_pixel[0] - (self.win_size - 1)/2)
		start_x = int(center_pixel[1] - (self.win_size - 1)/2)
		return start_y, start_x
	
	def _transform_image(self, x, data_point, start_y, start_x):
		x = TF.to_pil_image(x)
		x = TF.crop(x, start_y, start_x, self.win_size, self.win_size) # square
		x = TF.rotate(x, data_point.angle) if data_point.angle else x
		x = TF.hflip(x) if data_point.hflip else x
		x = TF.vflip(x) if data_point.vflip else x
		if self.image_tf is not None:
			x = self.image_tf(x)
		x = TF.to_tensor(x) # HWC->CHW; [0,255]->[0,1]
		if self.normalizer is not None:
			x = self.normalizer(x)
		return x
		
	def _transform_mask(self, x, data_point, start_y, start_x):
		x = TF.to_pil_image(x)
		if not self.make_one_hot:
			x = TF.to_grayscale(x)
		x = TF.crop(x, start_y, start_x, self.win_size, self.win_size) # square
		x = TF.rotate(x, data_point.angle) if data_point.angle else x
		x = TF.hflip(x) if data_point.hflip else x
		x = TF.vflip(x) if data_point.vflip else x
		x = TF.to_tensor(x) # HWC->CHW; [0,255]->[0,1]
		if self.mask_tf:
			x = self.mask_tf(x)
		return x
	
	def __call__(self, data_point):

		image = self.loaded_images[data_point.map_id]
		mask = self.loaded_masks[data_point.map_id]
		
		assert image.shape[:2] == mask.shape[:2]
		start_y, start_x = self._compute_patch_start_coords(image, data_point)
		
		if self.make_one_hot:
			values = np.unique(mask)
			mask_planes = [(mask == v) for v in values]
			mask = np.stack(mask_planes, axis=-1).astype(mask.dtype) * 255
		 
		image = self._transform_image(image, data_point, start_y, start_x)
		mask = self._transform_mask(mask, data_point, start_y, start_x)
				
		return {'images': image, 'masks': mask}
