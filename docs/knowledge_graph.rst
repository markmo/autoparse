Knowledge Graph
===============

Entities and links are add to a graph data structure for downstream analysis. A graph starts with
defining an ontology. (Although I would expect definitions and structure to evolve, up-front analysis
solves a number of early critical design decisions. For example, we expect the graph size to grow
(given the expected log volume) to require a clustered database environment. Understanding the schema
and access patterns will establish the appropriate partitioning key and secondary indexes for the
graph implementation.

Examples of ontologies is shown below.

.. image:: images/cysec_knowledge_graph.jpg

.. image:: images/cysec_ontology.jpg

.. image:: images/cysec_ontology_2.jpg

The example ontology shown above, consists of the following five entity types:

1. Vulnerability. Each of the records in the vulnerability database corresponds to an instance
   of a vulnerability type. Every vulnerability has its own unique CVE ID.
2. Assets. The assets include the software and the operating system (OS).
3. Software. This is a subclass-of assets (e.g., Adobe Reader).
4. OS. This is a subclass of assets (e.g., Ubuntu 14.04).
5. Attack. Most attacks can be regarded as an intrusion aimed at a certain vulnerability. The
   process of an attack can be a process of vulnerability exploitation.

See the paper, `A Practical Approach to Constructing a Knowledge Graph for Cybersecurity -
ScienceDirect <https://www.sciencedirect.com/science/article/pii/S2095809918301097>`_, for more information.
