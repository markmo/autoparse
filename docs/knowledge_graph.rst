Knowledge Graph
===============

Entities and links are add to a graph data structure for downstream analysis. A graph starts with
defining an ontology. (Although I would expect definitions and structure to evolve, up-front analysis
solves a number of early critical design decisions. For example, we expect the graph size to grow
(given the expected log volume) to require a clustered database environment. Understanding the schema
and access patterns will establish the appropriate partitioning key and secondary indexes for the
graph implementation.

Examples of ontologies is shown below.

.. raw:: html

    <img src="../images/cysec_knowledge_graph.jpg"/>

    <img src="../images/cysec_ontology.jpg" width="60%"/>

    <img src="../images/cysec_ontology_2.jpg" width="60%"/>

The example ontology shown above, consists of the following five entity types:

1. Vulnerability. Each of the records in the vulnerability database corresponds to an instance
   of a vulnerability type. Every vulnerability has its own unique CVE ID.
2. Assets. The assets include the software and the operating system (OS).
3. Software. This is a subclass-of assets (e.g., Adobe Reader).
4. OS. This is a subclass of assets (e.g., Ubuntu 14.04).
5. Attack. Most attacks can be regarded as an intrusion aimed at a certain vulnerability. The
   process of an attack can be a process of vulnerability exploitation.


Types of Analyses
-----------------

* Finding natural clusters (Refs: 3, 4)

* Predicting if a relationship exists between two nodes (‘link prediction’) (Refs: 2)

* Scoring and classification of nodes, edges and whole graphs

* Community detection


Concepts
--------

* Node2vec

  * **Homophily**. Similar nodes are located nearby.

    Examples:

    * Social network — we are more connected to people like us
    * Business location — financial firms, doctor offices or marketing companies seem to be typically
      located on the same street
    * Organizational structure — people on the same team share similar traits

  * **Structural equivalence**. Different communities share the same structure:

    * Organizational structure — while the teams can have weak connectivity, the structure of the team
      (manager, senior member, newcomers, junior members) is repeated from team to team.


References:
-----------

1. `A Practical Approach to Constructing a Knowledge Graph for Cybersecurity - ScienceDirect <https://www.sciencedirect.com/science/article/pii/S2095809918301097>`_

2. `Multi-hop knowledge graph reasoning learned via policy gradient with reward shaping and action dropout <https://github.com/salesforce/MultiHopKG>`_

3. `Node2Vec: Scalable Feature Learning for Networks <https://arxiv.org/pdf/1607.00653.pdf>`_

4. `Snap <https://github.com/snap-stanford/snap>`_

   A popular and fairly generalized embedding technique using random walks. (My interpretation:
   find clusters using the embeddings.) Using the “In-out” hyperparameter you can prioritise whether
   the walks focus on small local areas (e.g. are these nodes in the same small community?) or whether
   the walks wander broadly across the graph (e.g. are these nodes in the same type of structure?).

   The standard algorithm does not incorporate node properties or edge properties, amongst other
   desirable pieces of information.

5. `Relational inductive biases, deep learning, and graph networks <https://arxiv.org/abs/1806.01261>`_ (DeepMind)

   Embed a neural network into the graph structure itself.

6. `How to get started with machine learning on graphs <https://medium.com/octavian-ai/how-to-get-started-with-machine-learning-on-graphs-7f0795c83763>`_

7. `Graph Convolutional Networks <https://tkipf.github.io/graph-convolutional-networks/>`_

8. `Structure2Vec <https://github.com/Hanjun-Dai/pytorch_structure2vec>`_
