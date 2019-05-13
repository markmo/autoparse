from collections import defaultdict, OrderedDict
import json
import numpy as np
import pandas as pd
import re
import sklearn.utils as sk_utils


def load_event_sequences(data_dir, save_csv=False):
    data_dict = defaultdict(list)
    for file in data_dir.rglob('*.jsonl'):
        with file.open('r') as f:
            for line in f:
                j = json.loads(line.rstrip('\n'))
                params = j['params']
                for p in params:
                    if p['entity'] == 'ip_address':
                        data_dict[p['value']].append(j['event_id'])

    df = pd.DataFrame(list(data_dict.items()), columns=['ip_address', 'event_sequence'])
    if save_csv:
        df.to_csv('event_sequences.csv', index=False)

    return df['event_sequence'].values


def load_hdfs_dataset(log_filename, label_filename=None, window='session', test_ratio=.5, save_csv=False):
    """
    Load HDFS structured log into train and test datasets

    :param log_filename: (str) filename of structured log file
    :param label_filename: (str) filename of anomaly labels; None for unlabeled data
    :param window: (str) window option; default is 'session'
    :param test_ratio: ratio of test split
    :param save_csv:
    :return:
        (x_train, y_train) training data
        (x_test, y_test) test data
    """
    x_train = None
    y_train = None
    x_test = None
    y_test = None
    if log_filename.endswith('.npz'):
        data = np.load(log_filename)
        x_data = data['x_data']
        y_data = data['y_data']
        pos_idx = y_data > 0
        x_pos = x_data[pos_idx]
        y_pos = y_data[pos_idx]
        x_neg = x_data[~pos_idx]
        y_neg = y_data[~pos_idx]
        train_pos = int((1 - test_ratio) * x_pos.shape[0])
        train_neg = int((1 - test_ratio) * x_neg.shape[0])
        x_train = np.hstack([x_pos[0: train_pos], x_neg[0: train_neg]])
        y_train = np.hstack([y_pos[0: train_pos], y_neg[0: train_neg]])
        x_test = np.hstack([x_pos[train_pos:], x_neg[train_neg:]])
        y_test = np.hstack([y_pos[train_pos:], y_neg[train_neg:]])
    elif log_filename.endswith('.csv'):
        assert window == 'session', 'Only window="session" is supported for the HDFS dataset'
        struct_log = pd.read_csv(log_filename, engine='c', na_filter=False, memory_map=True)
        data_dict = OrderedDict()
        for i, row in struct_log.iterrows():
            blk_id_list = re.findall(r'(blk_-?\d+)', row['Content'])
            blk_id_set = set(blk_id_list)
            for blk_id in blk_id_set:
                if blk_id not in data_dict:
                    data_dict[blk_id] = []

                data_dict[blk_id].append(row['EventId'])

        data_df = pd.DataFrame(list(data_dict.items()), columns=['BlockId', 'EventSequence'])
        if label_filename:
            label_data = data_df[data_df['Label'] == 1].reset_index()
            label_data = label_data.set_index('BlockId')
            label_dict = label_data['Label'].to_dict()
            data_df['Label'] = data_df['BlockId'].apply(lambda x: 1 if label_dict[x] == 'Anomaly' else 0)

            # Split train and test data
            pos_data = data_df[data_df['Label'] == 1].reset_index()
            neg_data = data_df[data_df['Label'] == 0].reset_index()
            train_pos_num = int(len(pos_data) * (1 - test_ratio))
            train_neg_num = int(len(neg_data) * (1 - test_ratio))
            train_data = pd.concat([pos_data.loc[:train_pos_num - 1, :], neg_data.loc[:train_neg_num - 1, :]])
            train_data = sk_utils.shuffle(train_data)
            test_data = pd.concat([pos_data.loc[train_pos_num:, :], neg_data.loc[train_neg_num:, :]])
            x_train, y_train = train_data['EventSequence'].values, train_data['Label'].values
            x_test, y_test = test_data['EventSequence'].values, test_data['Label'].values

        if save_csv:
            data_df.to_csv('data_instances.csv', index=False)

        if not label_filename:
            print('Total: {} instances'.format(len(data_df)))
            x_data = data_df['EventSequence'].values
            return (x_data, None), (None, None)
    else:
        raise NotImplementedError('`load_hdfs` supports CSV and NPZ files only.')

    n_train = x_train.shape[0]
    n_test = x_test.shape[0]
    n_total = n_train + n_test
    n_train_pos = sum(y_train)
    n_test_pos = sum(y_test)
    n_pos = n_train_pos + n_test_pos

    print('Total: {} instances, {} anomalies, {} normal'.format(n_total, n_pos, n_total - n_pos))
    print('Train: {} instances, {} anomalies, {} normal'.format(n_train, n_train_pos, n_train - n_train_pos))
    print('Test: {} instances, {} anomalies, {} normal'.format(n_test, n_test_pos, n_test - n_test_pos))

    return (x_train, y_train), (x_test, y_test)
