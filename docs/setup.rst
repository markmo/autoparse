Setup Test Environment
======================

1. Setup test ELK stack

::

   docker run -p 5601:5601 -p 9200:9200 -p 5044:5044 -it --name elk sebp/elk

   or

   docker start elk

2. Open Kibana at http://localhost:5601

3. Download Spacy model if not already installed

::

   python -m spacy download en_core_web_sm

4. Install ArangoDB

   On OS X you can:
   ::

       brew install arangodb

   To start the server:
   ::

       /usr/local/Cellar/arangodb/3.4.4/sbin/arangod

5. Open the ArangoDB client at `http://localhost:8529 <http://localhost:8529>`_

