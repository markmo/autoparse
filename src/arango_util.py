import os

from arango import ArangoClient


def get_db():
    protocol = os.getenv('ARANGODB_PROTOCOL') or 'http'
    host = os.getenv('ARANGODB_HOST') or 'localhost'
    port = os.getenv('ARANGODB_PORT') or 8529
    dbname = os.getenv('ARANGODB_NAME') or 'cslogs'
    username = os.getenv('ARANGODB_USERNAME')
    password = os.getenv('ARANGODB_PASSWORD')
    client = ArangoClient(protocol=protocol, host=host, port=port)
    return client.db(dbname, username=username, password=password)
