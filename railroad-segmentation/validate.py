import torch
import torch.nn.functional as F
from torch import nn
from tqdm import tqdm
from utils import dice_coeff

MASK_THRESHOLD = 0.5

def validate_model(model, val_loader, n_val, device, writer=None, aux_branch=None):
	model.eval()

	# Binary Segmentation: Dice Coeff
	# Multi-class Segm   : Cross Entropy
	total_dice = 0

	with tqdm(total=n_val, desc='Validation', unit='batch', leave=False) as progress_bar:

		for v_batch in val_loader:
			images, masks = v_batch['images'], v_batch['masks']
			images = images.to(dtype=torch.float32, device=device)
			masks = masks.to(dtype=torch.float32, device=device)

			with torch.no_grad():
				pred_masks = model(images)
				if aux_branch is None:
					pred_masks = torch.sigmoid(pred_masks)
				else:
					pred_masks = torch.sigmoid(pred_masks['out'])
				pred_masks = (pred_masks > MASK_THRESHOLD).float()
				dc = dice_coeff(pred_masks, masks) # if multiclass, then use cross_entropy
				total_dice += dc
			progress_bar.update()

		total_dice = total_dice / n_val

	return total_dice