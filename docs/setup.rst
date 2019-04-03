Setup
=====

1. Setup test ELK stack

::

    docker run -p 5601:5601 -p 9200:9200 -p 5044:5044 -it --name elk sebp/elk

    or

    docker start elk

2. Open Kibana at http://localhost:5601