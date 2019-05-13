from argparse import ArgumentParser
from anomaly.data_util import load_event_sequences, load_hdfs_dataset
from anomaly.feature_extractor import FeatureExtractor
from anomaly.invariants_miner import InvariantsMiner
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR.parent / 'output'
STRUCT_LOG = ROOT_DIR / 'data/hdfs/HDFS_100k.log_structured.csv'


# noinspection PyUnusedLocal
def run(constants):
    x_train = load_event_sequences(DATA_DIR, save_csv=True)
    feature_extractor = FeatureExtractor()
    x_train = feature_extractor.fit_transform(x_train, term_weighting='tf-idf', normalization='zero-mean')

    print('Training')

    # Initialize one of the unsupervised models: PCA, LogClustering, or InvariantsMiner
    model = InvariantsMiner()

    # Model hyperparameters may be sensitive to log data
    model.fit(x_train)

    # Make predictions and manually check for correctness
    y_pred = model.predict(x_train)

    # Use the trained model for online anomaly detection
    print('Testing')

    # Load another new log file. Here we use `STRUCT_LOG` for demo only.
    (x_test, _), (_, _) = load_hdfs_dataset(str(STRUCT_LOG), window='session')

    # Use same feature extraction process as training - using `transform` instead
    x_test = feature_extractor.transform(x_test)

    # Make predictions
    y_pred = model.predict(x_test)


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Detect anomalies')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
