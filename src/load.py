"""
Load entities and relations into ArangoDB from a stream emitted by `parse.py`.
"""

import hashlib
import json
import sys
from argparse import ArgumentParser

from arango import ArangoClient

DB_NAME = 'cslogs'


def run(constants):
    client = ArangoClient(protocol='http', host='localhost', port=8529)
    sys_db = client.db('_system', username='root', password='')
    if not sys_db.has_database(DB_NAME):
        sys_db.create_database(DB_NAME)

    db = client.db(DB_NAME, username='root', password='password')
    # logs = db.create_collection('logs')
    # logs.add_hash_index(fields=['log_id'], unique=True)
    if not db.has_graph('logs'):
        graph = db.create_graph('logs')
    else:
        graph = db.graph('logs')

    logs = create_or_fetch_vertex_collection(graph, 'logs')
    log_keys = create_or_fetch_vertex_collection(graph, 'log_keys')
    ip_addrs = create_or_fetch_vertex_collection(graph, 'ip_addrs')
    filenames = create_or_fetch_vertex_collection(graph, 'filenames')
    uris = create_or_fetch_vertex_collection(graph, 'uris')
    urls = create_or_fetch_vertex_collection(graph, 'urls')
    emails = create_or_fetch_vertex_collection(graph, 'emails')
    devices = create_or_fetch_vertex_collection(graph, 'devices')
    procs = create_or_fetch_vertex_collection(graph, 'procs')
    mem_addrs = create_or_fetch_vertex_collection(graph, 'mem_addrs')
    uuids = create_or_fetch_vertex_collection(graph, 'uuids')
    has_log_key = create_or_fetch_edge_collection(graph, 'has_log_key',
                                                  from_vertex_collections=['logs'],
                                                  to_vertex_collections=['log_keys'])
    has_ip_addr = create_or_fetch_edge_collection(graph, 'has_ip_addr',
                                                  from_vertex_collections=['logs'],
                                                  to_vertex_collections=['ip_addrs'])
    has_filename = create_or_fetch_edge_collection(graph, 'has_filename',
                                                   from_vertex_collections=['logs'],
                                                   to_vertex_collections=['filenames'])
    has_uri = create_or_fetch_edge_collection(graph, 'has_uri',
                                              from_vertex_collections=['logs'],
                                              to_vertex_collections=['uris'])
    has_url = create_or_fetch_edge_collection(graph, 'has_url',
                                              from_vertex_collections=['logs'],
                                              to_vertex_collections=['urls'])
    has_email = create_or_fetch_edge_collection(graph, 'has_email',
                                                from_vertex_collections=['logs'],
                                                to_vertex_collections=['emails'])
    has_device = create_or_fetch_edge_collection(graph, 'has_device',
                                                 from_vertex_collections=['logs'],
                                                 to_vertex_collections=['devices'])
    has_proc = create_or_fetch_edge_collection(graph, 'has_proc',
                                               from_vertex_collections=['logs'],
                                               to_vertex_collections=['procs'])
    has_mem_addr = create_or_fetch_edge_collection(graph, 'has_mem_addr',
                                                   from_vertex_collections=['logs'],
                                                   to_vertex_collections=['mem_addrs'])
    has_uuid = create_or_fetch_edge_collection(graph, 'has_uuid',
                                               from_vertex_collections=['logs'],
                                               to_vertex_collections=['uuids'])
    if constants['is_stream']:
        for line in sys.stdin.readlines():
            log = json.loads(line.strip())
            log_id = log['log_id']
            event_id = str(log['event_id'])
            print('upsert log:', log_id, log['line'])
            upsert(logs, {
                '_key': log_id,
                'name': log_id,
                'line': log['line'],
                'message': log['message'],
                'metadata': log['metadata']
            })
            upsert(log_keys, {
                '_key': event_id,
                'name': event_id,
                'template': log['log_key']
            })
            has_log_key_key = '{}-{}'.format(log_id, event_id)
            upsert(has_log_key, {
                '_key': has_log_key_key,
                'name': has_log_key_key,
                '_from': 'logs/{}'.format(log_id),
                '_to': 'log_keys/{}'.format(event_id)
            })
            for param in log['params']:
                if param['entity'] == 'ip_address':
                    upsert_param(param, log_id, 'logs', ip_addrs, has_ip_addr)
                elif param['entity'] == 'file':
                    upsert_param(param, log_id, 'logs', filenames, has_filename)
                elif param['entity'] == 'uri':
                    upsert_param(param, log_id, 'logs', uris, has_uri)
                elif param['entity'] == 'url':
                    upsert_param(param, log_id, 'logs', urls, has_url)
                elif param['entity'] == 'email':
                    upsert_param(param, log_id, 'logs', emails, has_email)
                elif param['entity'] == 'device':
                    upsert_param(param, log_id, 'logs', devices, has_device)
                elif param['entity'] == 'process':
                    upsert_param(param, log_id, 'logs', procs, has_proc)
                elif param['entity'] == 'memory_address':
                    upsert_param(param, log_id, 'logs', mem_addrs, has_mem_addr)
                elif param['entity'] == 'uuid':
                    upsert_param(param, log_id, 'logs', uuids, has_uuid)
    else:
        raise NotImplementedError


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
        return graph.create_edge_definitions(edge_collection=collection_name, *kwargs)
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


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Load parsed logs')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
