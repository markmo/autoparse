import os

from arango import ArangoClient


class ArangoDb(object):

    def __init__(self, test=False):
        self.test = test
        self._client = None
        self._sys_db = None
        self._db = None

    @property
    def client(self):
        if self._client is None:
            if self.test:
                protocol = os.getenv('TEST_ARANGODB_PROTOCOL') or 'http'
                host = os.getenv('TEST_ARANGODB_HOST') or 'localhost'
                port = os.getenv('TEST_ARANGODB_PORT') or 8529
            else:
                protocol = os.getenv('ARANGODB_PROTOCOL') or 'http'
                host = os.getenv('ARANGODB_HOST') or 'localhost'
                port = os.getenv('ARANGODB_PORT') or 8529

            self._client = ArangoClient(protocol=protocol, host=host, port=port)

        return self._client

    @property
    def sys_db(self):
        if self._sys_db is None:
            if self.test:
                username = os.getenv('TEST_ARANGODB_SYS_USERNAME')
                password = os.getenv('TEST_ARANGODB_SYS_PASSWORD')
            else:
                username = os.getenv('ARANGODB_SYS_USERNAME')
                password = os.getenv('ARANGODB_SYS_PASSWORD')

            self._sys_db = self.client.db('_system', username=username, password=password)

        return self._sys_db

    @property
    def db(self):
        if self._db is None:
            if self.test:
                dbname = os.getenv('TEST_ARANGODB_NAME') or 'cslogs'
                username = os.getenv('TEST_ARANGODB_USERNAME')
                password = os.getenv('TEST_ARANGODB_PASSWORD')
            else:
                dbname = os.getenv('ARANGODB_NAME') or 'cslogs'
                username = os.getenv('ARANGODB_USERNAME')
                password = os.getenv('ARANGODB_PASSWORD')

            self._db = self.client.db(dbname, username=username, password=password)

        return self._db

    def create_database(self, dbname):
        if not self.sys_db.has_database(dbname):
            self.sys_db.create_database(dbname)

    def create_graph(self, graph_name):
        if not self.db.has_graph(graph_name):
            return self.db.create_graph(graph_name)

        return self.db.graph(graph_name)
