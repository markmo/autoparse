Node2vec
========

Node2vec is an algorithmic framework for representational learning on graphs. It produces node
embeddings that are learned in the same way as word2vec's embeddings, using a skip-gram model.

(Word2vec is used in NLP and Deep Learning for text to learn a vector representation for words,
which can be used to determine semantic similarity or to `compute word analogies <https://www.technologyreview.com/s/541356/king-man-woman-queen-the-marvelous-mathematics-of-computational-linguistics/>`_
such as "man is to king as woman is to ?".)

Word2vec embeddings are learned from a large corpus of text such as Wikipedia. Similarly, Node2vec
needs to generate a corpus from a graph. It does so using a sampling strategy.

Let's think about a corpus as a group of directed acyclic graphs with a maximum out-degree of 1.
This is like a text sentence where each word in the sentence is a node and it points to the next
word (node) in the sentence.

Most graphs though, aren't that simple. They can be (un)directed, (un)weighted, (a)cyclic, and are
basically more complex in structure than text.

To solve that, node2vec uses a tunable sampling strategy. It generates random walks from each node
of the graph.

.. raw:: html

    <img src="../../../images/node2vec.png" width="100%"/>

Node2vec's sampling strategy accepts four hyperparameters:

1. `n_walks` number of random walks to be generated from each node in the graph
2. `walk_length` number of nodes in each random walk
3. `P` return hyperparameter
4. `Q` in-out hyperparameter

And also the standard skip-gram hyperparameters such as context window size and number of iterations.

`Q` and `P` are better explained with a visualization.

Consider that you are on a random walk and have just transitioned from node `<t>` to node `<v>` in
the following diagram (taken from the article).

.. raw:: html

    <img src="../../../images/node2vec_transition.png" width="60%"/>

The probability of transition from `<v>` to any one of its neighbours is `<edge weight> x <alpha>`
(normalized), where `<alpha>` is determined by the hyperparameter settings.

`P` controls the probability of going back to `<t>` after visiting `<v>`.

`Q` controls the probability of exploring undiscovered parts of the graph.

Don't forget that edge weight is also taken into consideration, so the final transition probability
is a function of:

1. The previous node in the walk
2. `P` and `Q`
3. Edge weight

Using the above sampling strategy, node2vec will generate "sentences" (the directed subgraphs), which
will be used to learn embeddings just as text sentences are used in word2vec.
