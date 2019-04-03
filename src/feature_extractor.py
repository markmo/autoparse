from collections import Counter
import numpy as np
import pandas as pd
# noinspection PyUnresolvedReferences
from scipy.special import expit


class FeatureExtractor(object):

    def __init__(self):
        self.idf_vec = None
        self.mean_vec = None
        self.events = None
        self.term_weighting = None
        self.normalization = None
        self.oov = None

    def fit_transform(self, x_seq, term_weighting=None, normalization=None, oov=False, min_count=1):
        """
        Fit and transform the data matrix.

        :param x_seq: (ndarray) log sequences matrix
        :param term_weighting: (str) 'tf-idf' or None
        :param normalization: (str) 'zero-mean', 'sigmoid', or None
        :param oov: (bool) flag to use OOV event
        :param min_count: (int) minimum number of events (default: 1), valid only when oov=True
        :return: x_new: transformed data matrix
        """
        self.term_weighting = term_weighting
        self.normalization = normalization
        self.oov = oov
        x_counts = []
        for i in range(x_seq.shape[0]):
            event_counts = Counter(x_seq[i])
            x_counts.append(event_counts)

        x_df = pd.DataFrame(x_counts)
        x_df = x_df.fillna(0)
        self.events = x_df.columns
        x = x_df.values
        if self.oov:
            oov_vec = np.zeros(x.shape[0])
            if min_count > 1:
                idx = np.sum(x > 0, axis=0) >= min_count
                oov_vec = np.sum(x[:, ~idx] > 0, axis=1)
                x = x[:, idx]
                self.events = np.array(x_df.columns)[idx].tolist()

            x = np.hstack([x, oov_vec.reshape(x.shape[0], 1)])

        n_instances, n_events = x.shape
        if self.term_weighting == 'tf-idf':
            df_vec = np.sum(x > 0, axis=0)
            self.idf_vec = np.log(n_instances / (df_vec + 1e-8))
            idf_mat = x * np.tile(self.idf_vec, (n_instances, 1))
            x = idf_mat

        if self.normalization == 'zero-mean':
            mean_vec = x.mean(axis=0)
            self.mean_vec = mean_vec.reshape(1, n_events)
            x = x - np.tile(self.mean_vec, (n_instances, 1))
        elif self.normalization == 'sigmoid':
            x[x != 0] = expit(x[x != 0])

        x_new = x
        print('Train data shape: {}-by-{}\n'.format(x_new.shape[0], x_new.shape[1]))
        return x_new

    def transform(self, x_seq):
        """
        Transform the data matrix using trained parameters.

        :param x_seq: log sequences matrix
        :return: x_new: transformed data matrix
        """
        x_counts = []
        for i in range(x_seq.shape[0]):
            event_counts = Counter(x_seq[i])
            x_counts.append(event_counts)

        x_df = pd.DataFrame(x_counts)
        x_df = x_df.fillna(0)
        empty_events = set(self.events) - set(x_df.columns)
        for event in empty_events:
            x_df[event] = [0] * len(x_df)

        x = x_df[self.events].values
        if self.oov:
            oov_vec = np.sum(x_df[x_df.columns.difference(self.events)].values > 0, axis=1)
            x = np.hstack([x, oov_vec.reshape([x.shape[0], 1])])

        n_instances, n_events = x.shape
        if self.term_weighting == 'tf-idf':
            idf_mat = x * np.tile(self.idf_vec, (n_instances, 1))
            x = idf_mat

        if self.normalization == 'zero_mean':
            x = x - np.tile(self.mean_vec, (n_instances, 1))
        elif self.normalization == 'sigmoid':
            x[x != 0] = expit(x[x != 0])

        x_new = x
        print('Test data shape: {}-by-{}\n'.format(x_new.shape[0], x_new.shape[1]))
        return x_new
