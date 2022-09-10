import numpy as np

import re

from .common import *
import logging as lg

class CH(CVI):
    """
    The stateful information of the Calinski-Harabasz (CH) Cluster Validity Index
    """

    # # References
    # 1. L. E. Brito da Silva, N. M. Melton, and D. C. Wunsch II, "Incremental Cluster Validity Indices for Hard Partitions: Extensions  and  Comparative Study," ArXiv  e-prints, Feb 2019, arXiv:1902.06711v1 [cs.LG].
    # 2. T. Calinski and J. Harabasz, "A dendrite method for cluster analysis," Communications in Statistics, vol. 3, no. 1, pp. 1–27, 1974.
    # 3. M. Moshtaghi, J. C. Bezdek, S. M. Erfani, C. Leckie, and J. Bailey, "Online Cluster Validity Indices for Streaming Data," ArXiv e-prints, 2018, arXiv:1801.02937v1 [stat.ML]. [Online].
    # 4. M. Moshtaghi, J. C. Bezdek, S. M. Erfani, C. Leckie, J. Bailey, "Online cluster validity indices for performance monitoring of streaming data clustering," Int. J. Intell. Syst., pp. 1-23, 2018.
    # """
    # Calinski-Harabasz (CH) Cluster Validity Index.
    # """

    def __init__(self):
        """
        CH initialization routine.
        """
        # """
        # Test documentation.
        # """
        super().__init__()

        return
        # print("Hello world!")
        # self.data = []

    # def param_inc(self, sample:np.ndarray, label:np.ndarray):
    def param_inc(self, sample:np.ndarray, label:int):
        i_label = self.label_map.get_internal_label(label)

        n_samples_new = self.n_samples + 1
        if not self.mu.any():
            mu_new = sample
            self.setup(sample)
        else:
            mu_new = (1 - 1/n_samples_new) * self.mu + (1/n_samples_new) * sample

        # Correct for python 0-indexing
        if i_label + 1 > self.n_clusters:
            n_new = 1
            v_new = sample
            CP_new = 0.0
            G_new = np.zeros(self.dim)
            # Update 1-D parameters with list appends
            self.n_clusters += 1
            self.n.append(n_new)
            self.CP.append(CP_new)

            # Update 2-D parameters with numpy appends
            # self.v = np.append(self.v, v_new, axis=0)
            # self.G = np.append(self.G, G_new, axis=0)
            self.v = np.vstack([self.v, v_new])
            self.G = np.vstack([self.G, G_new])
        else:
            n_new = self.n[i_label] + 1
            v_new = (1 - 1/n_new) * self.v[i_label, :] + (1/n_new) * sample
            # lg.info(v_new)
            delta_v = self.v[i_label, :] - v_new
            diff_x_v = sample - v_new
            CP_new = self.CP[i_label] + np.transpose(diff_x_v[np.newaxis])
            G_new = self.G[i_label, :] + diff_x_v + self.n[i_label] * delta_v
            # Update parameters
            self.n[i_label] = n_new
            self.v[i_label, :] = v_new
            self.CP[i_label] = CP_new
            self.G[i_label, :] = G_new

        self.n_samples = n_samples_new
        self.mu = mu_new
        self.SEP = [self.n[ix] * sum((self.v[ix, :] - self.mu)**2) for ix in range(self.n_clusters)]

        return

    def param_batch(self, data:np.ndarray, labels:np.ndarray):
        self.dim, self.n_samples = data.shape
        # Take the average across all samples, but cast to 1-D vector
        self.mu = np.mean(data, axis=0)
        u = np.unique(labels)
        self.n_clusters = u.size
        self.n = np.zeros(self.n_clusters, dtype=int)
        self.v = np.zeros(self.n_clusters, self.dim)
        self.CP = np.zeros(self.n_clusters)
        self.SEP = np.zeros(self.n_clusters)

        for ix in range(self.n_clusters):
            subset = data[lambda x: labels[x] == ix, :]
            self.n[ix] = subset.shape[0]
            self.v[ix, :] = np.mean(subset, axis=0)
            diff_x_v = subset - self.v[ix, :] * np.ones((self.n[ix], 1))
            self.CP[ix] = np.sum(diff_x_v ** 2)
            self.SEP[ix] = self.n[ix] * np.sum((self.v[ix, :] - self.mu) **2)

        return

    def evaluate(self):
        if self.n_clusters > 2:
            # Within group sum of scatters
            self.WGSS = sum(self.CP)
            # Between groups sum of scatters
            self.BGSS = sum(self.SEP)
            # CH index value
            self.criterion_value = (self.BGSS / self.WGSS) * ((self.n_samples - self.n_clusters)/(self.n_clusters - 1))
        else:
            self.BGSS = 0.0
            self.criterion_value = 0.0

        return