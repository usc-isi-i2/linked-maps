import numpy as np
import matplotlib.pyplot as plt

from collections import deque, Counter
from kneed import KneeLocator
from .components import find_components
from . import imagify

def n_components(data):
	'''
		1) Imagify (Binarize)
		2) Find Components using DFS
	'''
	
	image, fig = imagify.create_image(data)
	image_components = find_components(image)
	imagify.delete_image()
	return len(image_components)


def percentage_noise(data, clusters):
	'''
		1) Imagify (Binarize)
		2) Find Components using DFS + Determine Convex Hulls
		3) Map data to pixels in image using matplotlib
		4) Assign components to each pixel, by one of the following methods:
			a) finding closest component using level order search (8-adj)
			b) finding closest hull (distance of each pix with hull)
			c) finding smallest hull that contains the pixel (vectorized)
				- since DBSCAN produces small clusters, instead of mapping
				  all data points, we're mapping only repr points and
				  taking majority voting over them to choose the component
		5) Knee Detection on #pixels in each component
			% Noise = [#pixels(components after knee)] / [#total_data_pixels]
	'''

	'''
	# Method 1: Searching
	component_ids_grid = np.full(image.shape, -1)
	for ix, component in enumerate(image_components):
		for pix in component.members:
			component_ids_grid[pix] = ix
	'''

	'''
	# Method 2: Closest Hull
	for point in data:
		...
		pix = (int(round(pix[0])), int(round(pix[1])))[::-1]
		comp = self.component_ids_grid[pix]
		if comp == -1:
			comp = self.image_components[self.find_nearest_component(pix)]
		else:
			comp = self.image_components[comp]
		comp.data_points.append(point)
	'''
	
	image, figure = imagify.create_image(data)
	image_components = find_components(image, hull=True)
	geocoor2pixel = figure.gca().axes.transData.transform_point
	
	# Map geocoordinates to pixels and assign them to image components
	sorted_image_components = sorted(image_components, key=lambda x:x.volume, reverse=True)
	for cluster in clusters:
		counter = Counter()

		for r_point in cluster.representatives:
			pix = geocoor2pixel(r_point)[::-1]
			comp = None # The compactest one that contains the point or the closest one

			for c in sorted_image_components:
				hull = c.convex_hull
				inside = True
				for i in range(1, hull.vertices.shape[0]):
					res = cross_product(hull.points[hull.vertices[i-1]], hull.points[hull.vertices[i]], pix)
					if res < 0:
						inside = False
						break
				if inside:
					comp = c
			
			if comp is None: # couldn't find one that contains the pixel
				comp = find_closest_hull(pix, image_components)
			counter[comp] = counter.setdefault(comp, 0) + 1

		comp = counter.most_common(1)[0][0]
		comp.data_points.extend(cluster.points.tolist())

	imagify.delete_image()
	
	distribution = sorted([len(c.data_points) for c in image_components], reverse=True)
	# distribution = sorted([c.volume for c in image_components], reverse=True)
	
	assert sum(distribution) == data.shape[0]

	if len(distribution) < 2:
		# kneedle needs at least 2 points in dist
		return 0

	x = range(len(distribution))

	kneedle = KneeLocator(x, distribution, curve='convex', direction='decreasing', online=False, S=0)
	if kneedle.knee is None:
		return 0

	# kneedle.plot_knee()
	k = kneedle.knee
	print('Knee: ', k, end=' + ')
	try:
		kneedle = KneeLocator(x[:-k], distribution[k:], curve='convex', direction='decreasing', online=False, S=0)
		print(kneedle.knee, end=' = ')
	except:
		kneedle.knee = None
	if kneedle.knee is None:
		knee = k
	else:
		knee = k + kneedle.knee
		# kneedle.plot_knee()
	print(knee)
	noise = sum(distribution[knee+1:])/sum(distribution)
	return noise



def cross_product(o, a, b):
	return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def find_closest_hull(pixel, components):
	# Find closest component by computing distance from their hulls

	closest = None
	d = np.inf
	p3 = np.asarray(pixel)

	for component in components:
		hull = component.convex_hull
		simplices = hull.points[hull.simplices]
		p1 = simplices[:, 0, :]
		p2 = simplices[:, 1, :]
		calc = (np.abs(np.cross(p2-p1, p1-p3)) / np.linalg.norm(p2-p1)).min()
		if d > calc:
			d = calc
			closest = component
	return closest


def search_closest_component(pixel, components, figure, component_ids_grid):
	# Finds closest component for a pixel in the image grid using
	# level order search in 8-adj. Accurate, but painfully slow.

	NEIGHBORS = ((-1,0), (0,1), (1,0), (0,-1), (1,-1), (1,1), (1,-1), (-1,-1)) # 8-adjacency

	cols, rows = figure.canvas.get_width_height()
	
	possible_components = []
	visited = set()
	queue = deque()
	
	queue.append(pixel)
	queue.append(None)

	while any(queue):
		cell = queue.popleft()
		if cell is None:
			if any(possible_components):
				break
			else:
				queue.append(None)
				continue
				
		if cell in visited:
			continue
		visited.add(cell)
		
		if component_ids_grid[cell] != -1:
			possible_components.append(component_ids_grid[cell])
		
		i, j = cell
		neighbors = [(i+x,j+y) for x,y in NEIGHBORS if i+x>=0 and i+x<rows\
												and j+y>=0 and j+y<cols]
		for neighbor in neighbors:
			if neighbor not in visited:
				queue.append(neighbor)
				
	comps, counts = np.unique(possible_components, return_counts=True)
	return comps[counts.argmax()] # majority voting in 8-adj
	# return comps[np.argmax(np.asarray([len(components[c].members) for c in comps]))] # largest possible component

