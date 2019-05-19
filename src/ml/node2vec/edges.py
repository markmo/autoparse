from abc import ABC, abstractmethod
from functools import reduce
from itertools import combinations_with_replacement

from gensim.models import KeyedVectors
import numpy as np
from tqdm import tqdm


class EdgeEmbedder(ABC):

    def __init__(self, keyed_vectors, quiet=False):
        """

        :param keyed_vectors: (KeyedVectors) containing nodes and embeddings to calculate edge embeddings
        :param quiet:
        """
        self.keyed_vectors = keyed_vectors
        self.quiet = quiet

    @abstractmethod
    def _embed(self, edge):
        """
        Abstract embedding method
        :param edge: (tuple) of two nodes
        :return: (np.ndarray) Edge embedding
        """
        pass

    def __getitem__(self, item):
        if not isinstance(item, tuple) or not len(item) == 2:
            raise ValueError('Edge must be a tuple of two nodes')

        if item[0] not in self.keyed_vectors.index2word:
            raise KeyError('Node {} does not exist in given KeyedVectors'.format(item[0]))

        if item[1] not in self.keyed_vectors.index2word:
            raise KeyError('Node {} does not exist in given KeyedVectors'.format(item[1]))

        return self._embed(item)

    def as_keyed_vectors(self):
        """
        Generate a KeyedVectors instance with all nodes
        :return:
        """
        generator = combinations_with_replacement(self.keyed_vectors.index2word, r=2)
        if not self.quiet:
            vocab_size = len(self.keyed_vectors.vocab)
            total_size = (reduce(lambda x, y: x * y, range(1, vocab_size + 2)) /
                          (2 * reduce(lambda x, y: x * y, range(1, vocab_size))))
            generator = tqdm(generator, desc='Generating edge features', total=total_size)

        # Generate features
        tokens = []
        features = []
        for edge in generator:
            token = str(tuple(sorted(edge)))
            embedding = self._embed(edge)
            tokens.append(token)
            features.append(embedding)

        # Build KeyedVectors instance
        edge_kv = KeyedVectors(vector_size=self.keyed_vectors.vector_size)
        edge_kv.add(entities=tokens, weights=features)

        return edge_kv


class AverageEmbedder(EdgeEmbedder):
    """ Averaged node features """

    def _embed(self, edge):
        return (self.keyed_vectors[edge[0]] + self.keyed_vectors[edge[1]]) / 2


class HadamardEmbedder(EdgeEmbedder):
    """ Hadamard product of node features """

    def _embed(self, edge):
        return self.keyed_vectors[edge[0]] * self.keyed_vectors[edge[1]]


class WeightedL1Embedder(EdgeEmbedder):
    """ Weighted L1 node features """

    def _embed(self, edge):
        return np.abs(self.keyed_vectors[edge[0]] - self.keyed_vectors[edge[1]])


class WeightedL2Embedder(EdgeEmbedder):
    """ Weighted L2 node features """

    def _embed(self, edge):
        return (self.keyed_vectors[edge[0]] - self.keyed_vectors[edge[1]]) ** 2
