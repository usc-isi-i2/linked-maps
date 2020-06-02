from sklearn import metrics
from itertools import combinations, product
import numpy as np

class Healthiness:
	'''
	* Calculate health scores for clusters
	* Health of a cluster depends on:
		- its density: #points in it
		- its neighborhood: (exponentially decaying 'z')
			-> Density of k closest neighbors (clusters)
			-> Standardized distance
	'''

	def __init__(self, clusters, k_nearest_clusters=3, z=1, basis='representors', linkage='single'):
		self.clusters = clusters
		self.k_nearest_clusters = k_nearest_clusters
		self.z = z # Exponentially decaying factor in soft voting
		self.basis = basis
		self.linkage = linkage


	def calculate_neighbor_distances(self):
		''' Compute the distance matrix for clusters '''
		
		neighbors_matrix = np.diag([-1 for _ in range(len(self.clusters))]).astype('float64')
		np.fill_diagonal(neighbors_matrix, np.inf)

		for c1, c2 in combinations(enumerate(self.clusters), 2):
			i, j = c1[0], c2[0]
			c1, c2 = c1[1], c2[1]
			
			if self.basis == 'centroid':
				distance = np.sqrt(np.sum((c1.representatives - c2.representatives)**2))
			elif self.basis == 'medoid':
				distance = np.sqrt(np.sum((c1.representatives - c2.representatives)**2))
				distance = distance.min() # in case there are m > 1 medoids, then choose the min one
			elif self.basis == 'representors':
				distance = metrics.euclidean_distances(c1.representatives, c2.representatives)
				if self.linkage == 'single':
					distance = distance.min()
				elif self.linkage == 'complete':
					distance = distance.max()
				elif self.linkage == 'average':
					distance = distance.mean()
				
			neighbors_matrix[i,j] = distance
			neighbors_matrix[j,i] = distance
		self.neighbor_distances = neighbors_matrix
			
		
	def determine_neighborhood(self):
		''' Find k nearest clusters '''
		self.neighborhood = self.neighbor_distances.argsort()[:, :self.k_nearest_clusters]
			
			
	def compute_health_scores(self, mean_cluster_size):
		k_neighbor_distances = []
		health_scores = []
		
		for i, cluster in enumerate(self.clusters):
			k_indices = self.neighborhood[i]
			k_neighbor_distances.append(self.neighbor_distances[i][k_indices])
		
		k_neighbor_distances = np.asarray(k_neighbor_distances)
		k_neighbor_distances = k_neighbor_distances / k_neighbor_distances.mean(axis=0) # Standardize distances
		
		for i, cluster in enumerate(self.clusters):
			neighborhood_health = 0
			
			for k, dist in enumerate(k_neighbor_distances[i]):
				neighbor = self.clusters[self.neighborhood[i,k]]
				cluster.neighbors.append(neighbor)
				n_health = neighbor.n_points / k_neighbor_distances[i,k]
				n_health *= (1 / (k+1)**self.z) # Discount factor
				neighborhood_health += n_health
			
			health = (cluster.n_points / mean_cluster_size) * neighborhood_health
			
			cluster.neighborhood_health = neighborhood_health
			cluster.health = health
			health_scores.append(health)

		self.health_scores = health_scores


	def calculate_healthiness(self, mean_cluster_size):
		self.calculate_neighbor_distances()
		self.determine_neighborhood()
		self.compute_health_scores(mean_cluster_size)


	def get_healthy_clusters(self, reverse=True):
		clusters = sorted(enumerate(self.clusters), key=lambda x: self.health_scores[x[0]], reverse=reverse)
		clusters = [c[1] for c in clusters]
		health_scores = sorted(self.health_scores, reverse=reverse)
		return clusters, health_scores

