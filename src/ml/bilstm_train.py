from argparse import ArgumentParser
from pathlib import Path
import os

import numpy as np

from ml.bilstm import BiLstmPredictor
from ml.bilstm_config import config
from ml.util import extract_text_model, load_url_data, merge_dict, plot_and_save_history
import settings

ROOT = Path(__file__).parent.parent.parent


def run(constant_overwrites):
    constants = merge_dict(config, constant_overwrites)
    random_state = 42
    embed_dim = constants['embed_dim']
    batch_size = constants['batch_size']
    epochs = constants['epochs']
    data_path = ROOT / os.getenv('DATA_DIR')
    model_path = ROOT / os.getenv('MODELS_DIR')
    report_path = ROOT / os.getenv('REPORTS_DIR')
    np.random.seed(random_state)
    url_data = load_url_data(data_path, sample=False)
    text_model = extract_text_model(url_data['url'])
    text_model['embed_dim'] = embed_dim
    classifier = BiLstmPredictor()
    history = classifier.fit(model=text_model, model_dir_path=model_path, url_data=url_data,
                             batch_size=batch_size, epochs=epochs)
    model_name = BiLstmPredictor.model_name
    report_filename = model_name + '-history.png'
    plot_and_save_history(history, model_name, str(report_path / report_filename))


if __name__ == '__main__':
    parser = ArgumentParser(description='Train Malicious URL Classifier')
    parser.add_argument('--embed-dim', dest='embed_dim', type=int, help='embedding size')
    parser.add_argument('--batch-size', dest='batch_size', type=int, help='batch size')
    parser.add_argument('--epochs', dest='epochs', type=int, help='number epochs')
    args = parser.parse_args()
    run(vars(args))
