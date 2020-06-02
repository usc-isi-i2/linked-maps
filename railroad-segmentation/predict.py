import cv2
import numpy as np
import os
import torch
from torchvision import transforms
from utils import make_batch, plot_overlay
import tifffile

MASK_THRESHOLD = 0.5
STRIDE = 50
BATCH_SIZE = 10
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

# tf = transforms.Compose([
# 		transforms.ToPILImage(),
# 		transforms.ToTensor(),
# 		transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
# 	])


def predict(model, image_path, win_size, normalize=False, aux_branch=None):
	image_path = os.path.realpath(image_path)
	extension = os.path.splitext(image_path)[-1]
	model.eval()
	
	if extension.startswith('.tif'):
		image = tifffile.imread(image_path)
	else:
		image = cv2.imread(image_path)
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	output_mask = np.zeros((image.shape[:2]), dtype=np.uint8)
	
	normalizer = transforms.Compose([transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

	for (img_batch, coords) in make_batch(image, win_size, STRIDE, batch_size=BATCH_SIZE):
		if normalize:
			img_batch = normalizer(normalize)
		img_batch = img_batch.to(dtype=torch.float32, device=DEVICE)

		with torch.no_grad():
			if aux_branch is None:
				pred = model(img_batch)
			else:
				pred = model(img_batch)['out']
			pred = torch.sigmoid(pred)
			pred = (pred > MASK_THRESHOLD).to(dtype=torch.uint8) * 255
			# for i in range(pred.shape[0]):
				# plot_overlay(img_batch[i], pred[i])
			pred = pred.squeeze()
			pred = pred.cpu().numpy()

			for i in range(img_batch.shape[0]):
				(s_y, e_y), (s_x, e_x) = coords[i]
				output_mask[s_y:e_y, s_x:e_x] = np.logical_or(output_mask[s_y:e_y, s_x:e_x], pred[i])
			
	image_path, image_name = os.path.split(image_path)
	output_image_path = os.path.join(image_path, 'pred_'+image_name)

	if extension.startswith('.tif'):
		tifffile.imwrite(output_image_path, output_mask)
	else:
		cv2.imwrite(output_image_path, output_mask)
