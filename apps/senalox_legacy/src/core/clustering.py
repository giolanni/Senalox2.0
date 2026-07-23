from sklearn.cluster import KMeans
import numpy as np

class NumberClusterAnalyzer:
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)  # Aggiungi n_init

    def analyze(self, estrazioni):
        # Crea una matrice di one-hot encoding delle estrazioni
        matrix = np.zeros((len(estrazioni), 90))
        for i, e in enumerate(estrazioni):
            for num in e.numeri:
                matrix[i, num - 1] = 1

        # Esegui il clustering
        clusters = self.model.fit_predict(matrix)

        # Trova i numeri più frequenti in ogni cluster
        cluster_nums = {}
        for cluster in range(self.n_clusters):
            cluster_matrix = matrix[clusters == cluster]
            frequencies = cluster_matrix.sum(axis=0)
            cluster_nums[cluster] = np.argsort(frequencies)[-6:][::-1] + 1

        return cluster_nums
