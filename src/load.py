"""
Load entities and relations into ArangoDB from a stream emitted by `parse.py`.
"""

import hashlib
import json
import os
import sys
from argparse import ArgumentParser

from arango_util import ArangoDb
import settings
from streaming_app import app, parsed_logs_topic


class GraphLoader(object):

    def __init__(self):
        arango = ArangoDb(test=True)
        dbname = os.getenv('TEST_ARANGODB_NAME') or 'cslogs'
        arango.create_database(dbname)
        # logs = db.create_collection('logs')
        # logs.add_hash_index(fields=['log_id'], unique=True)
        graph = arango.create_graph('logs')
        self.collections = create_or_fetch_vertex_collection(graph, 'collections')
        self.logs = create_or_fetch_vertex_collection(graph, 'logs')
        self.log_keys = create_or_fetch_vertex_collection(graph, 'log_keys')
        self.ip_addrs = create_or_fetch_vertex_collection(graph, 'ip_addrs')
        self.filenames = create_or_fetch_vertex_collection(graph, 'filenames')
        self.uris = create_or_fetch_vertex_collection(graph, 'uris')
        self.urls = create_or_fetch_vertex_collection(graph, 'urls')
        self.emails = create_or_fetch_vertex_collection(graph, 'emails')
        self.devices = create_or_fetch_vertex_collection(graph, 'devices')
        self.procs = create_or_fetch_vertex_collection(graph, 'procs')
        self.mem_addrs = create_or_fetch_vertex_collection(graph, 'mem_addrs')
        self.uuids = create_or_fetch_vertex_collection(graph, 'uuids')
        self.users = create_or_fetch_vertex_collection(graph, 'users')
        self.people = create_or_fetch_vertex_collection(graph, 'people')
        self.organizations = create_or_fetch_vertex_collection(graph, 'organizations')
        self.locations = create_or_fetch_vertex_collection(graph, 'locations')
        self.has_log = create_or_fetch_edge_collection(graph, 'has_log',
                                                       from_vertex_collections=['collections'],
                                                       to_vertex_collections=['logs'])
        self.has_log_key = create_or_fetch_edge_collection(graph, 'has_log_key',
                                                           from_vertex_collections=['logs'],
                                                           to_vertex_collections=['log_keys'])
        self.has_ip_addr = create_or_fetch_edge_collection(graph, 'has_ip_addr',
                                                           from_vertex_collections=['logs'],
                                                           to_vertex_collections=['ip_addrs'])
        self.has_filename = create_or_fetch_edge_collection(graph, 'has_filename',
                                                            from_vertex_collections=['logs'],
                                                            to_vertex_collections=['filenames'])
        self.has_uri = create_or_fetch_edge_collection(graph, 'has_uri',
                                                       from_vertex_collections=['logs'],
                                                       to_vertex_collections=['uris'])
        self.has_url = create_or_fetch_edge_collection(graph, 'has_url',
                                                       from_vertex_collections=['logs'],
                                                       to_vertex_collections=['urls'])
        self.has_email = create_or_fetch_edge_collection(graph, 'has_email',
                                                         from_vertex_collections=['logs'],
                                                         to_vertex_collections=['emails'])
        self.has_device = create_or_fetch_edge_collection(graph, 'has_device',
                                                          from_vertex_collections=['logs'],
                                                          to_vertex_collections=['devices'])
        self.has_proc = create_or_fetch_edge_collection(graph, 'has_proc',
                                                        from_vertex_collections=['logs'],
                                                        to_vertex_collections=['procs'])
        self.has_mem_addr = create_or_fetch_edge_collection(graph, 'has_mem_addr',
                                                            from_vertex_collections=['logs'],
                                                            to_vertex_collections=['mem_addrs'])
        self.has_uuid = create_or_fetch_edge_collection(graph, 'has_uuid',
                                                        from_vertex_collections=['logs'],
                                                        to_vertex_collections=['uuids'])
        self.has_user = create_or_fetch_edge_collection(graph, 'has_user',
                                                        from_vertex_collections=['logs'],
                                                        to_vertex_collections=['users'])
        self.has_person = create_or_fetch_edge_collection(graph, 'has_person',
                                                          from_vertex_collections=['logs'],
                                                          to_vertex_collections=['people'])
        self.has_organization = create_or_fetch_edge_collection(graph, 'has_organization',
                                                                from_vertex_collections=['logs'],
                                                                to_vertex_collections=['organizations'])
        self.has_location = create_or_fetch_edge_collection(graph, 'has_location',
                                                            from_vertex_collections=['logs'],
                                                            to_vertex_collections=['locations'])

    # TODO buffer updates for batch execution
    def load(self, jsonstr):
        try:
            log = json.loads(jsonstr.strip())
            log_id = log['log_id']
            event_id = str(log['event_id'])
            source_collection = log['source_collection']
            source_id = log['id']
            metadata = log['metadata']
            metadata['source_id'] = source_id
            collkey = hashlib.md5(source_collection.encode('utf-8')).hexdigest()[0:8]
            if not self.collections.has(collkey):
                self.collections.insert({
                    '_key': collkey,
                    'name': source_collection
                })

            # print('upsert log:', log_id, log['line'])
            upsert(self.logs, {
                '_key': log_id,
                'name': log_id,
                'line': log['line'],
                'message': log['message'],
                'metadata': metadata
            })
            upsert(self.log_keys, {
                '_key': event_id,
                'name': event_id,
                'template': log['log_key']
            })
            has_log_key_ = '{}-{}'.format(collkey, log_id)
            upsert(self.has_log, {
                '_key': has_log_key_,
                'name': has_log_key_,
                '_from': 'collections/{}'.format(collkey),
                '_to': 'logs/{}'.format(log_id)
            })
            has_log_key_key = '{}-{}'.format(log_id, event_id)
            upsert(self.has_log_key, {
                '_key': has_log_key_key,
                'name': has_log_key_key,
                '_from': 'logs/{}'.format(log_id),
                '_to': 'log_keys/{}'.format(event_id)
            })
            last_user = None
            for param in log['params']:
                if param['entity'] == 'ip_address':
                    upsert_param(param, log_id, 'logs', self.ip_addrs, self.has_ip_addr)
                elif param['entity'] == 'file':
                    upsert_param(param, log_id, 'logs', self.filenames, self.has_filename)
                elif param['entity'] == 'uri':
                    upsert_param(param, log_id, 'logs', self.uris, self.has_uri)
                elif param['entity'] == 'url':
                    upsert_param(param, log_id, 'logs', self.urls, self.has_url)
                elif param['entity'] == 'email':
                    upsert_param(param, log_id, 'logs', self.emails, self.has_email)
                elif param['entity'] == 'device':
                    upsert_param(param, log_id, 'logs', self.devices, self.has_device)
                elif param['entity'] == 'process':
                    upsert_param(param, log_id, 'logs', self.procs, self.has_proc)
                elif param['entity'] == 'memory_address':
                    upsert_param(param, log_id, 'logs', self.mem_addrs, self.has_mem_addr)
                elif param['entity'] == 'uuid':
                    upsert_param(param, log_id, 'logs', self.uuids, self.has_uuid)
                elif param['entity'] == 'user':
                    upsert_param(param, log_id, 'logs', self.users, self.has_user)
                    last_user = hashlib.md5(param['value'].encode('utf-8')).hexdigest()[0:8]
                elif param['entity'] == 'password':
                    if last_user is not None:
                        upsert(self.users, {'_key': last_user, 'password': param['value']})
                elif param['entity'] == 'PERSON':
                    upsert_param(param, log_id, 'logs', self.people, self.has_person)
                elif param['entity'] == 'ORG':
                    upsert_param(param, log_id, 'logs', self.organizations, self.has_organization)
                elif param['entity'] in ['GPE', 'LOC']:
                    upsert_param(param, log_id, 'logs', self.locations, self.has_location)

            return log

        except Exception as e:
            raise e

    def process_stdin(self):
        for jsonstr in sys.stdin.readlines():
            log = self.load(jsonstr)
            print(log)


def upsert_param(param, root_id, root_name, vertex_coll, edge_coll):
    entity = param['value']
    entity_hash = hashlib.md5(entity.encode('utf-8')).hexdigest()[0:8]
    upsert(vertex_coll, {
        '_key': entity_hash,
        'name': entity,
        'span': [param['char_start'], param['char_end']],
        'token': param['token_start']
    })
    upsert(edge_coll, {
        '_key': '{}-{}'.format(root_id, entity_hash),
        'name': '{}-{}'.format(root_id, entity),
        '_from': '{}/{}'.format(root_name, root_id),
        '_to': '{}/{}'.format(vertex_coll.name, entity_hash)
    })


def create_or_fetch_edge_collection(graph, collection_name, **kwargs):
    if not graph.has_edge_definition(collection_name):
        return graph.create_edge_definition(collection_name,
                                            kwargs['from_vertex_collections'],
                                            kwargs['to_vertex_collections'])
    else:
        return graph.edge_collection(collection_name)


def create_or_fetch_vertex_collection(graph, collection_name):
    if not graph.has_vertex_collection(collection_name):
        return graph.create_vertex_collection(collection_name)
    else:
        return graph.vertex_collection(collection_name)


# ArangoDB now supports 'repsert' ops
# (https://docs.arangodb.com/devel/Manual/ReleaseNotes/NewFeatures34.html#repsert-operation)
def upsert(resource, props):
    key = props['_key']
    if resource.has(key):
        resource.update(props)
    else:
        resource.insert(props)


loader = GraphLoader()


@app.agent(parsed_logs_topic)
async def load(parsed_logs):
    async for jsonstr in parsed_logs:
        loader.load(jsonstr)


def run(constants):
    if constants['is_stream']:
        loader.process_stdin()
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Load parsed logs')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
