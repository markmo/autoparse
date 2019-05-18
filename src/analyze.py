import json
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

from arango import ArangoClient

from ml.bilstm import BiLstmPredictor
import settings

ROOT = Path(__file__).parent.parent


def scan_for_malicious_urls(constants):
    model_path = ROOT / os.getenv('MODELS_DIR')
    predictor = BiLstmPredictor()
    predictor.load_model(model_path)
    if constants['is_stream']:
        for line in sys.stdin.readlines():
            log = json.loads(line.strip())
            for param in log['params']:
                if param['entity'] == 'url':
                    pred = predictor.predict(param['value'])
                    if pred == 1:  # bad
                        param['meta'] = {'malicious_warning': True}
                    else:
                        param['meta'] = {'malicious_warning': False}

            print(log)

    else:
        db = get_db()
        aql = db.aql
        cursor = aql.execute('for doc in urls return doc')
        bad_urls = []
        for doc in cursor:
            pred = predictor.predict(doc.name)
            if pred == 1:  # bad
                doc['malicious_warning'] = True
                bad_urls.append(doc.name)
            else:
                doc['malicious_warning'] = False

            db.update_document(doc)


def get_db():
    protocol = os.getenv('ARANGODB_PROTOCOL') or 'http'
    host = os.getenv('ARANGODB_HOST') or 'localhost'
    port = os.getenv('ARANGODB_PORT') or 8529
    dbname = os.getenv('ARANGODB_NAME') or 'cslogs'
    username = os.getenv('ARANGODB_USERNAME')
    password = os.getenv('ARANGODB_PASSWORD')
    client = ArangoClient(protocol=protocol, host=host, port=port)
    return client.db(dbname, username=username, password=password)


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Analyze graph')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    scan_for_malicious_urls(vars(args))
