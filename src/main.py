import json
import os
from pathlib import Path

from arango import ArangoClient

import settings
from streaming_app import app
from load import load
from parse import parse

ROOT = Path(__file__).parent.parent


# testing purposes
# @app.task
# async def send_text_logs(app):
#     with open(ROOT / 'input.jsonl', 'r') as f:
#         for line in f:
#             await parse.send(value=line)


@app.task
async def crawl_arango(app):
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
                        await parse.send(value=json.dumps({
                            'id': doc[coll_info['id_field']],
                            'source_collection': collname,
                            'line': line,
                            'metadata': metadata
                        }))
