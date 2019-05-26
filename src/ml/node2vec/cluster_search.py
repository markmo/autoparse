from pathlib import Path

import networkx as nx

import settings
from arango_util import ArangoDb
from ml.node2vec.node2vec import Node2vec

ROOT = Path(__file__).parent.parent.parent.parent


class ClusterSearch(object):

    def __init__(self):
        g = build_local_graph()

        self.node2vec = Node2vec(g, embed_dim=64, walk_length=30, n_walks=200, workers=4)

        # Note: if the graph is too big to fit in memory, pass `temp_folder`, which will
        # initiate `sharedmem` in `Parallel`. This will be slower on smaller graphs. E.g.
        # node2vec = Node2vec(g, embed_dim=64, walk_length=30, n_walks=200, workers=4, temp_folder='/tmp/sharedmem')

        self.model = None

    def fit(self):
        # Any keyword argument accepted by gensim.Word2Vec can be passed
        # `dimensions` and `workers` are automatically passed from the Node2vec constructor
        self.model = self.node2vec.fit(window=10, min_count=1, batch_words=4)

    def most_similar_nodes(self):
        # Look for most similar nodes
        return self.model.wv.most_similar('2')

    def save_embeddings(self, embeddings_filename):
        # Save embeddings for later use
        self.model.wv.save_word2vec_format(embeddings_filename)

    def save(self, model_filename):
        # Save model for later use
        self.model.save(model_filename)


# TODO use Foxx to run in Arango
# Can I use external functions in Foxx, or would I need to implement Node2vec in Foxx?
# Currently, exporting data from ArangoDB into a local representation using NetworkX
def build_local_graph():
    g = nx.Graph()
    arango = ArangoDb()
    db = arango.db
    logs = db.graph('logs')
    edge_names = [x['edge_collection'] for x in logs.edge_definitions()]
    for name in logs.vertex_collections():
        coll = db.collection(name)
        for node in coll.all():
            g.add_node(node['_id'], line=node['line'])
            for edge_name in edge_names:
                edges = logs.edges(edge_name, node['_id'], direction='out')['edges']
                for edge in edges:
                    g.add_edge(edge['_from'], edge['_to'], id=edge['_id'])

    return g


def print_most_similar(nodes):
    if nodes:
        for node in nodes:
            print(node)


if __name__ == '__main__':
    model = ClusterSearch()
    model.fit()

    most_similar = model.most_similar_nodes()
    print_most_similar(most_similar)

    _embeddings_filename = str(ROOT / 'models' / 'node2vec.embed')
    _model_filename = str(ROOT / 'models' / 'node2vec.model')
    model.save_embeddings(_embeddings_filename)
    model.save(_model_filename)
