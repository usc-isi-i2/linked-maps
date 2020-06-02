import numpy as np
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.cluster.cure import cure
# from matplotlib.colors import XKCD_COLORS as COLORS
# COLORS = list(COLORS.keys())

class Cluster:
	''' Represents cluster of geocoordinates '''
	c_count = 0
	
	def __init__(self, points, dbscan_label):
		self.points = np.asarray(points)
		self.dbscan_label = dbscan_label
#         self.color = COLORS[Cluster.c_count]
		
		self.representatives = None # That represent the cluster {c, m ,r}
		
		self.health = None
		self.neighborhood_health = None
		self.neighbors = list() # List of clusters
		
		self.cid = Cluster.c_count
		Cluster.c_count += 1
		
		
	def __del__(self):
		if Cluster.c_count:
			Cluster.c_count -= 1
			
			
	def get_centroid(self):
		''' Mean value of the objects in the cluster'''
		return self.points.mean(axis=0)
		
	
	def get_medoids(self, m=1):
		''' Most centrally located objects in the cluster '''
		m = min(self.n_points, m)
		initial_medoids = list(range(m)) # Random
		medoids = kmedoids(self.points, initial_medoids).process().get_medoids()
		medoids = self.points[np.asarray(self.medoids)]
		return medoids
		
	
	def get_representors(self, r=4):
		''' Point representors of the cluster '''
		r = min(self.n_points, r)
		c = cure(self.points, number_cluster=1, number_represent_points=r, compression=0)
		representors = np.asarray(c.process().get_representors()[0])
		return representors
		
	
	def set_representative_points(self, basis, n=None):
		repr_points = None
		if basis == 'centroid':
			repr_points = self.get_centroid()
		elif basis == 'medoids':
			repr_points = (self.get_medoids() if n is None else self.get_medoids(n))
		elif basis == 'representors':
			repr_points = (self.get_representors() if n is None else self.get_representors(n))
		self.representatives = repr_points
		
	
	def __repr__(self):
		if hasattr(self, 'color'):
			return "Cluster {} <{}> [{}]".format(self.cid, ''.join(self.color.split(':')[-1:]), self.n_points)
		else:
			return "Cluster {} [{}]".format(self.cid, self.n_points)

	def __str__(self):
		if hasattr(self, 'color'):
			return "Cluster {} <{}> [{}]".format(self.cid, ''.join(self.color.split(':')[-1:]), self.n_points)
		else:
			return "Cluster {} [{}]".format(self.cid, self.n_points)
			
	@property
	def n_points(self):
		return self.points.shape[0]
