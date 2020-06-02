import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
from validate import validate_model
import os

AUX_LOSS_WEIGHT = 0.4


def train_model(model, train_loader, val_loader, n_train, n_val,
		criterion, optimizer, scheduler, lr,
		n_epochs, device, checkpoints_dir, aux_branch=None,
	):

	writer = SummaryWriter()
	total_iterations = 0

	try:
		for epoch in range(n_epochs):
			model.train() # just lets it know that now in training 'mode' (eg. manage BN/dropout behaviours)
			
			epoch_loss = 0
			
			with tqdm(total=n_train, desc=f'Epoch {epoch + 1}/{n_epochs}', unit='img') as progress_bar:
				
				for step, batch in enumerate(train_loader):
					images, masks = batch['images'], batch['masks']
					
					# typecasting masks to float32 because n_classes = 1
					# if n_classes > 1, then masks would've been `long`
					images = images.to(dtype=torch.float32, device=device)
					masks = masks.to(dtype=torch.float32, device=device)
					
					pred_masks = model(images)
	
					if aux_branch is None:
						loss = criterion(pred_masks, masks)
					else:
						# print(pred_masks.keys())
						# print(pred_masks['aux'].shape)
						# print(pred_masks['out'].shape)
						loss = criterion(pred_masks['out'], masks)
						loss = criterion(pred_masks['aux'], masks) * AUX_LOSS_WEIGHT + loss
						
					epoch_loss += loss.item()
					writer.add_scalar('Loss/train', loss.item(), total_iterations)
					
					progress_bar.set_postfix(**{'loss (batch)': loss.item()})
					
					optimizer.zero_grad()
					loss.backward()
	#                 nn.utils.clip_grad_value_(model.parameters(), 0.1)
					optimizer.step()
					
					progress_bar.update(images.shape[0]) # update tqdm
					total_iterations += 1
					
					if total_iterations % 10 == 0:
						# for tag, value in model.named_parameters():
							# tag = tag.replace('.', '/')
							# writer.add_histogram(f'weights/{tag}', value.data.cpu().numpy(), total_iterations)
							# writer.add_histogram(f'grads/{tag}', value.grad.cpu().numpy(), total_iterations)

						model.eval()
						evaluation_loss = validate_model(model, val_loader, n_val, device, writer, aux_branch)
						model.train()
						
						scheduler.step(evaluation_loss)
						writer.add_scalar('learning_rate', optimizer.param_groups[0]['lr'], total_iterations)
						writer.add_scalar('Dice/test', evaluation_loss, total_iterations)
						
			# Save checkpoints after each epoch
			torch.save(model.state_dict(), os.path.join(checkpoints_dir, f'epoch_{epoch+1}.pth'))
			
	except KeyboardInterrupt:
		torch.save(model.state_dict(), 'INTERRUPTED.pth')	

	finally:
		writer.close()
	
