import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from kneed import KneeLocator

from cluster import Cluster
from health import Healthiness
from estimator import estimate
from utils import preprocess

class AgglomerativeDenoiser:

	def __init__(self, k_nearest_clusters=3, z=0.5,\
				 basis='representors', linkage='single', n_representatives=None):
		self.data = None
		self.clusters = list()
		self.noise = list()

		self.k_nearest_clusters = k_nearest_clusters
		self.z = z

		self.basis = basis
		self.linkage = linkage
		self.n_representatives = n_representatives

	@property
	def n_clusters(self):
		return len(self.clusters)

	@property
	def mean_cluster_size(self):
		return self.data.shape[0] / self.n_clusters


	def form_clusters(self):
		self.clusters.clear()
		self.noise.clear()

		n_clusters = estimate.n_components(self.data)
		clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage=self.linkage)
		clusterer.fit(self.data)

		for i in range(n_clusters):
			points = self.data[clusterer.labels_ == i]
			self.clusters.append(Cluster(points, i))

		for cluster in self.clusters:
			cluster.set_representative_points(self.basis, self.n_representatives)


	def density_denoising(self, reverse=True):
		clusters = sorted(self.clusters, key=lambda x: x.n_points, reverse=reverse)
		points = [c.n_points for c in clusters]
		return clusters, points


	def health_denoising(self, reverse=True):
		healthiness = Healthiness(self.clusters, k_nearest_clusters=self.k_nearest_clusters, z=self.z)
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


	def denoise(self, shapefile, decimals=6, basis='density', reverse=True, plot=True, update=False, **kwargs):
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

		x, y = range(len(clusters)), distribution

		if not reverse:
			kneedle = KneeLocator(x, y, direction='increasing', curve='convex', online=True, S=0)
			knee = kneedle.knee or 0
			noisy_clusters = clusters[:knee]
			healthy_clusters = clusters[knee:]
		else:
			kneedle = KneeLocator(x, y, direction='decreasing', curve='convex', online=True, S=0)
			knee = kneedle.knee or len(clusters)
			healthy_clusters = clusters[:knee]
			noisy_clusters = clusters[knee:]

		if kneedle.knee:
			if plot:
				kneedle.plot_knee()
				self.plot_comparisons(healthy_clusters, noisy_clusters)
			data, noise = self.segregate(healthy_clusters, noisy_clusters)
			self.noise.extend(noise)
			if update:
				self.data = np.asarray(data)#.round(decimals)
			return noise
