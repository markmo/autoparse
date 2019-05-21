import os
import random
from collections import defaultdict

import numpy as np
from gensim.models import Word2Vec
from joblib import delayed, Parallel
from tqdm import tqdm


class Node2vec(object):

    FIRST_TRAVEL_KEY = 'first_travel'
    PROBABILITIES_KEY = 'probabilities'
    NEIGHBOURS_KEY = 'neighbours'
    WEIGHT_KEY = 'weight'
    N_WALKS_KEY = 'n_walks'
    WALK_LENGTH_KEY = 'walk_length'
    P_KEY = 'p'
    Q_KEY = 'q'

    def __init__(self, graph, embed_dim=128, walk_length=90, n_walks=10, p=1, q=1, weight_key='weight',
                 workers=1, sampling_strategy=None, quiet=False, temp_folder=None):
        """
        Initializes the Node2Vec object, precomputing walking probabilities and generating the walks.
        :param graph: input graph
        :param embed_dim: (int) embedding dimension (default: 128)
        :param walk_length: (int) number of nodes in each walk (default: 80)
        :param n_walks: (int) number of walks per node (default: 10)
        :param p: (float) return hyperparameter (default: 1)
        :param q: (float) input hyperparameter (default: 1)
        :param weight_key: (str) key for the weight attribute on weighted graphs (default: 'weight')
        :param workers: (int) number of workers for parallel execution (default: 1)
        :param sampling_strategy: (dict) node specific sampling strategy; supports setting node specific `q`,
               `p`, `n_walks` and `walk_length`. Use these keys exactly. If not set, will use the global
               ones passed on object initialization.
        :param quiet: (bool) verbosity of logging
        :param temp_folder: (str) Path to folder with enough space to hold the memory map of
               `self.d_graph` (for big graphs); to be passed to `joblib.Parallel.temp_folder`
        """
        self.graph = graph
        self.embed_dim = embed_dim
        self.walk_length = walk_length
        self.n_walks = n_walks
        self.p = p
        self.q = q
        self.weight_key = weight_key
        self.workers = workers
        self.sampling_strategy = sampling_strategy or {}
        self.quiet = quiet
        self.d_graph = defaultdict(dict)
        self.temp_folder = None
        self.require = None
        if temp_folder:
            if not os.path.isdir(temp_folder):
                raise NotADirectoryError('{} does not exist or is not a directory'.format(temp_folder))

            self.temp_folder = temp_folder
            self.require = 'sharedmem'

        self._precompute_probabilities()
        self.walks = self._generate_walks()

    def _precompute_probabilities(self):
        """ Precomputes transition probabilities for each node """
        d_graph = self.d_graph
        first_travel_done = set()
        generator = self.graph.nodes() if self.quiet else \
            tqdm(self.graph.nodes(), desc='Computing transition probabilities')

        for source in generator:
            # init probabilities dict for first travel
            if self.PROBABILITIES_KEY not in d_graph[source]:
                d_graph[source][self.PROBABILITIES_KEY] = {}

            for current_node in self.graph.neighbours(source):
                # init probabilities dict
                if self.PROBABILITIES_KEY not in d_graph[current_node]:
                    d_graph[current_node][self.PROBABILITIES_KEY] = {}

                unnormalized_weights = []
                first_travel_weights = []
                d_neighbours = []

                # Calculate unnormalized weights
                for dest in self.graph.neighbours(current_node):
                    if current_node in self.sampling_strategy:
                        p = self.sampling_strategy[current_node].get(self.P_KEY, self.p)
                        q = self.sampling_strategy[current_node].get(self.Q_KEY, self.q)
                    else:
                        p = self.p
                        q = self.q

                    if dest == source:  # backward probability
                        ss_weight = self.graph[current_node][dest].get(self.weight_key, 1) / p
                    elif dest in self.graph[source]:  # the neighbour is connected to the source
                        ss_weight = self.graph[current_node][dest].get(self.weight_key, 1)
                    else:
                        ss_weight = self.graph[current_node][dest].get(self.weight_key, 1) / q

                    # Assign the unnormalized sampling strategy weight,
                    # normalize during the random walk
                    unnormalized_weights.append(ss_weight)
                    if current_node not in first_travel_done:
                        first_travel_weights.append(self.graph[current_node][dest].get(self.weight_key, 1))

                    d_neighbours.append(dest)

                # Normalize
                unnormalized_weights = np.array(unnormalized_weights)
                d_graph[current_node][self.PROBABILITIES_KEY][source] = (
                        unnormalized_weights / unnormalized_weights.sum())

                if current_node not in first_travel_done:
                    unnormalized_weights = np.array(first_travel_weights)
                    d_graph[current_node][self.FIRST_TRAVEL_KEY] = (
                            unnormalized_weights / unnormalized_weights.sum())
                    first_travel_done.add(current_node)

                # Save neighbours
                d_graph[current_node][self.NEIGHBOURS_KEY] = d_neighbours

    def _generate_walks(self):
        """
        Generates the random walks that will be used as the skip-gram input.
        :return: (list) of walks. Each walk is a list of nodes.
        """
        def flatten(l):
            return [it for sublist in l for it in sublist]

        # Split n_walks for each worker
        n_walks_lists = np.array_split(range(self.n_walks), self.workers)

        walk_results = Parallel(n_jobs=self.workers, temp_folder=self.temp_folder, require=self.require)(
            delayed(parallel_generate_walks)(
                self.d_graph,
                self.walk_length,
                len(n_walks),
                i,
                self.sampling_strategy,
                self.N_WALKS_KEY,
                self.WALK_LENGTH_KEY,
                self.NEIGHBOURS_KEY,
                self.PROBABILITIES_KEY,
                self.FIRST_TRAVEL_KEY,
                self.quiet
            ) for i, n_walks in enumerate(n_walks_lists, 1))

        return flatten(walk_results)

    def fit(self, **skip_gram_params):
        """
        Create the embeddings using gensim word2vec
        :param skip_gram_params: (dict) parameters for `gensim.models.Word2Vec` (do not supply `size`
               as it is taken from the Node2Vec `embed_dim` parameter)
        :return: (gensim.models.Word2Vec)
        """
        if 'workers' not in skip_gram_params:
            skip_gram_params['workers'] = self.workers

        if 'size' not in skip_gram_params:
            skip_gram_params['size'] = self.embed_dim

        return Word2Vec(self.walks, **skip_gram_params)


def parallel_generate_walks(d_graph, global_walk_length, n_walks, n_cpu, sampling_strategy=None,
                            n_walks_key=None, walk_length_key=None, neighbours_key=None,
                            probabilities_key=None, first_travel_key=None, quiet=False):
    """
    Generates the random walks that will be used as input to the skip-gram model.
    :param d_graph:
    :param global_walk_length:
    :param n_walks:
    :param n_cpu:
    :param sampling_strategy:
    :param n_walks_key:
    :param walk_length_key:
    :param neighbours_key:
    :param probabilities_key:
    :param first_travel_key:
    :param quiet:
    :return: (list) of walks. Each walk is a list of nodes.
    """
    walks = []
    pbar = None
    if not quiet:
        pbar = tqdm(total=n_walks, desc='Generating walks (n_cpu: {})'.format(n_cpu))

    for i in range(n_walks):
        # Update progress bar
        if not quiet:
            pbar.update(1)

        # Shuffle the nodes
        shuffled_nodes = list(d_graph.keys())
        random.shuffle(shuffled_nodes)

        # Start a random walk from every node
        for source in shuffled_nodes:
            # Skip nodes with specific n_walks
            if (source in sampling_strategy and
                    n_walks_key in sampling_strategy[source] and
                    sampling_strategy[source][n_walks_key] <= i):
                continue

            # Start walk
            walk = [source]

            # Calculate walk length
            if source in sampling_strategy:
                walk_length = sampling_strategy[source].get(walk_length_key, global_walk_length)
            else:
                walk_length = global_walk_length

            # Walk
            while len(walk) < walk_length:
                walk_options = d_graph[walk[-1]].get(neighbours_key, None)

                # Skip dead-end nodes
                if not walk_options:
                    break

                if len(walk) == 1:  # For the first step
                    probabilities = d_graph[walk[-1]][first_travel_key]
                    walk_to = np.random.choice(walk_options, size=1, p=probabilities)[0]
                else:
                    probabilities = d_graph[walk[-1]][probabilities_key][walk[-2]]
                    walk_to = np.random.choice(walk_options, size=1, p=probabilities)[0]

                walk.append(walk_to)

            walk = list(map(str, walk))  # Convert all to strings
            walks.append(walk)

    if not quiet:
        pbar.close()

    return walks
