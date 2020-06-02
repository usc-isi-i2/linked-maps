import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator

from cluster import Cluster
from health import Healthiness
from estimator import estimate
from utils import preprocess

class DBSCANDenoiser:

	def __init__(self, k_nearest_points=5, k_nearest_clusters=3, \
				basis='representors', linkage='single', z=1, \
				n_representatives=None, remove_dbscan_noise=False):

		self.data = None
		self.clusters = list()
		self.noise = list()

		self.k_nearest_points = k_nearest_points
		self.k_nearest_clusters = k_nearest_clusters
		self.remove_dbscan_noise = remove_dbscan_noise

		self.basis = basis
		self.linkage = linkage
		self.n_representatives = n_representatives
		self.z = z # Exponential factor in soft voting

	@property
	def n_clusters(self):
		return len(self.clusters)
	
	@property
	def mean_cluster_size(self):
		return self.data.shape[0] / self.n_clusters
	
	@property
	def median_cluster_size(self):
		dist = sorted([c.n_points for c in self.clusters])
		if len(dist) % 2 == 0:
			n = len(dist)//2
			return (dist[n] + dist[n+1]) / 2
		else:
			return dist[len(dist)//2]


	def form_clusters(self):
		''' 
		Forms densest clusters using DBSCAN; 
		If remove_dbscan_noise=False, then ignores DBSCAN -1 labelling of noise
		'''
		
		self.clusters.clear()
		self.noise.clear()
		
		nn = NearestNeighbors(n_neighbors=self.k_nearest_points)
		nn.fit(self.data)
		closest_distances, closest_neighbors = nn.kneighbors()
		
		# eps is the mean distance from kth neighbor (upper bound)
		eps = closest_distances.mean(axis=0)[-1]
		
		# Applying DBSCAN Clustering
		dbscan = DBSCAN(eps=eps, min_samples=2, metric='euclidean')
		labels = dbscan.fit_predict(self.data)
		unique_labels, label_counts = np.unique(labels, return_counts=True)
		
		for label, count in zip(unique_labels, label_counts):
			if label == -1:
				noise = self.data[labels == label]
				if self.remove_dbscan_noise:
					# These definitely are the noise because couldn't even pair up
					print("Initial Noise Removed:", count)
					# plt.figure()
					# plt.scatter(self.data[:, 0], self.data[:, 1], color='red')
					# plt.scatter(noise[:, 0], noise[:, 1], color='black')
					self.noise.extend(noise.tolist())
				else:
					# each noisy point will be a cluster of its own
					for point in noise:
						c = Cluster(np.asarray([point]), label)
						self.clusters.append(c)
				continue
				
			points = self.data[labels==label]
			c = Cluster(points, label)
			self.clusters.append(c)

		for cluster in self.clusters:
			cluster.set_representative_points(self.basis, self.n_representatives)
			

	def density_denoising(self, reverse=True):
		clusters = sorted(self.clusters, key=lambda x: x.n_points, reverse=reverse)
		points = [c.n_points for c in clusters]
		return clusters, points


	def health_denoising(self, reverse=True):
		healthiness = Healthiness(self.clusters, k_nearest_clusters=self.k_nearest_clusters, z=self.z, \
					basis=self.basis, linkage=self.linkage)
		healthiness.calculate_healthiness(self.mean_cluster_size)
		clusters, health_scores = healthiness.get_healthy_clusters(reverse=reverse)
		return clusters, health_scores


	def plot_comparisons(self, healthy_clusters, noisy_clusters):
		plt.figure()
		plt.subplot(1,3,1)
		plt.title("Original")
		plt.scatter(self.data[:, 0], self.data[:, 1], color='red')
		plt.tight_layout()
		plt.xticks([])
		plt.yticks([])

		plt.subplot(1,3,2)
		for i, cluster in enumerate(noisy_clusters):
			plt.scatter(cluster.points[:, 0], cluster.points[:, 1], color='black', label='noise')
		for i, cluster in enumerate(healthy_clusters):
			plt.scatter(cluster.points[:, 0], cluster.points[:, 1], color='red')
		plt.tight_layout()
		plt.xticks([])
		plt.yticks([])

		plt.subplot(1,3,3)
		plt.title("Denoised")
		for cluster in healthy_clusters:
			plt.scatter(cluster.points[:, 0], cluster.points[:, 1], color='red')
		plt.tight_layout()
		plt.xticks([])
		plt.yticks([])
		plt.show()


	def segregate(self, healthy_clusters, noisy_clusters):
		noise, data = list(), list()
		for cluster in noisy_clusters:
			noise.extend(cluster.points.tolist())

		for cluster in healthy_clusters:
			data.extend(cluster.points.tolist())

		# for point in self.data:
			# if point.tolist() not in noise:
				# data.append(point)
		return data, noise
	
		
	def denoise(self, shapefile, explain=None, decimals=6, basis='density', reverse=False, plot=True, update=False):
		self.data = preprocess(shapefile, decimals=decimals)
		self.form_clusters()

		if plot:
			plt.figure()
			plt.scatter(self.data[:, 0], self.data[:, 1])
			plt.show()

		if basis == 'density':
			clusters, distribution = self.density_denoising(reverse)

		elif basis == 'health':
			clusters, distribution = self.health_denoising(reverse)

		if explain is None:
			p_noise = estimate.percentage_noise(self.data, clusters) or 0
			print("Noise Estimated:", p_noise)
			explain = 1 - p_noise

		data_accounted = 0
		split = len(clusters)

		if not reverse:
			clusters = clusters[::-1]

		for i, cluster in enumerate(clusters):
			if data_accounted >= explain:
				split = i
				break
			data_accounted += (cluster.n_points / self.data.shape[0])
		
		healthy_clusters, noisy_clusters = clusters[:split], clusters[split:]
		data, noise = self.segregate(healthy_clusters, noisy_clusters)

		if plot:
			self.plot_comparisons(healthy_clusters, noisy_clusters)

		self.noise.extend(noise)
		if update:
			self.data = np.asarray(data)#.round(decimals)
		return noise

