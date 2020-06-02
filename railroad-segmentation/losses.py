import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


def dice_coeff(pred, target):
	eps = 1e-7
	pred, target = pred.view(-1), target.view(-1)
	numerator = 2 * torch.dot(pred, target)
	denominator = torch.square(pred).sum() + torch.square(target).sum()
	coeff = numerator.float() / (denominator.float() + eps)
	return coeff


class DiceLoss(nn.Module):
	def __init__(self, smooth=1.):
		self.smooth = smooth

	def forward(self, pred, target):
		pred, target = pred.view(-1), target.view(-1)
		numerator = 2 * torch.dot(pred, target)
		denominator = torch.square(pred).sum() + torch.square(target).sum()
		coeff = (numerator.float() + self.smooth) / (denominator.float() + self.smooth)
		return 1 - coeff
