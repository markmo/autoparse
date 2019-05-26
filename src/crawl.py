import json
import os
from argparse import ArgumentParser
from pathlib import Path

from arango import ArangoClient

import settings

ROOT = Path(__file__).parent.parent


def run(constants):
    with open(ROOT / 'src' / 'crawl_config.json', 'r') as f:
        config = json.load(f)

    if config['host'] and len(config['host']) > 0:
        protocol, host = config['host'].split('://')
        port = config['port']
    else:
        protocol = os.getenv('ARANGODB_PROTOCOL')
        host = os.getenv('ARANGODB_HOST')
        port = os.getenv('ARANGODB_PORT')

    client = ArangoClient(protocol=protocol, host=host, port=port)
    db = client.db(password=os.getenv('ARANGODB_PASSWORD'))
    if constants['is_stream']:
        for coll_info in config['collections']:
            collname = coll_info['name']
            coll = db.collection(collname)
            for doc in coll.all():
                metadata = {}
                for key in coll_info['prop_fields']:
                    if key in doc:
                        metadata[key] = doc[key]

                for key in coll_info['text_fields']:
                    if key in doc:
                        field = doc[key]
                        items = field if type(field) == list else field.splitlines()
                        for line in items:
                            print(json.dumps({
                                'id': doc[coll_info['id_field']],
                                'source_collection': collname,
                                'line': line,
                                'metadata': metadata
                            }))
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Load parsed logs')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
