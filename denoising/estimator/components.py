import numpy as np
from collections import deque
from scipy.spatial import ConvexHull

NEIGHBORS = ((-1,0), (0,1), (1,0), (0,-1), (1,-1), (1,1), (1,-1), (-1,-1)) # 8-adjacency

class Component:
	''' Represents cluster of pixels '''

	def __init__(self):
		self.members = list()
		self.convex_hull = None
		self.data_points = list()
		
	def determine_hull(self):
		if not any(self.members):
			return
		self.convex_hull = ConvexHull(self.members)
		
	def __str__(self):
		return "<#{} A:{}>".format(len(self.members), self.area)
	
	def __repr__(self):
		return str(self)
	
	@property
	def area(self):
		return self.convex_hull.area if self.convex_hull else None
	
	@property
	def volume(self):
		return self.convex_hull.volume if self.convex_hull else None



def find_components(image, hull=False):#, value=1):
	''' Find the connected components in the pixel grid '''

	def dfs_traversal(coor, component):
		if coor in visited:
			return

		d = deque()
		d.appendleft(coor)

		while any(d):
			top = d.popleft()
			if top in visited:
				continue
			visited.add(top)
			component.members.append(top)
			i, j = top
			neighbors = [(i+x,j+y) for x,y in NEIGHBORS if i+x>=0 and i+x<rows\
												and j+y>=0 and j+y<cols]
			neighbors = [neighbor for neighbor in neighbors if grid[neighbor[0]][neighbor[1]]]# == value]
			for neighbor in neighbors:
				if neighbor not in visited:
					d.append(neighbor)
					
	grid = image
	# print("Values:", np.unique(grid))
	rows = len(grid)
	if rows == 0: return 0
	cols = len(grid[0])

	components = []
	visited = set()

	for r in range(rows):
		for c in range(cols):
			if (r,c) in visited:
				continue
			if grid[r][c]:# == value:
				component = Component()
				dfs_traversal((r,c), component)
				if hull:
					component.determine_hull()
				components.append(component)
	return components
