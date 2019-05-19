from pathlib import PosixPath
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from keras.callbacks import History, ModelCheckpoint
from keras.layers import Bidirectional, Dense, Embedding, LSTM, SpatialDropout1D
from keras.models import Model, Sequential
from sklearn.model_selection import train_test_split


def make_bilstm_model(n_input_tokens: int, max_len: int, embed_dim: int) -> Model:
    model = Sequential()
    model.add(Embedding(input_dim=n_input_tokens, output_dim=embed_dim, input_length=max_len))
    model.add(SpatialDropout1D(0.2))
    model.add(Bidirectional(LSTM(units=64, dropout=0.2, recurrent_dropout=0.2, input_shape=(max_len, embed_dim))))
    model.add(Dense(2, activation='softmax'))
    model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


class BiLstmPredictor(object):

    model_name = 'bilstm'

    def __init__(self):
        self.model = None
        self.n_input_tokens = None
        self.idx2char = None
        self.char2idx = None
        self.max_url_seq_length = None
        self.embed_dim = None

    @staticmethod
    def get_config_path(model_dir_path: PosixPath) -> str:
        config_filename = BiLstmPredictor.model_name + '-config.npy'
        return str(model_dir_path / config_filename)

    @staticmethod
    def get_weights_path(model_dir_path: PosixPath) -> str:
        weights_filename = BiLstmPredictor.model_name + '-weights.h5'
        return str(model_dir_path / weights_filename)

    @staticmethod
    def get_arch_path(model_dir_path: PosixPath) -> str:
        arch_filename = BiLstmPredictor.model_name + '-arch.json'
        return str(model_dir_path / arch_filename)

    def load_model(self, model_dir_path: PosixPath) -> None:
        config_file_path = self.get_config_path(model_dir_path)
        weight_file_path = self.get_weights_path(model_dir_path)
        config = np.load(config_file_path).item()
        self.n_input_tokens = config['n_input_tokens']
        self.max_url_seq_length = config['max_url_seq_length']
        self.embed_dim = config['embed_dim']
        self.idx2char = config['idx2char']
        self.char2idx = config['char2idx']
        self.model = make_bilstm_model(self.n_input_tokens, self.max_url_seq_length, self.embed_dim)
        self.model.load_weights(weight_file_path)

    def predict(self, url: str) -> np.ndarray:
        x = np.zeros((1, self.max_url_seq_length))
        for idx, ch in enumerate(url):
            if ch in self.char2idx:
                x[0, idx] = self.char2idx[ch]

        predicted = self.model.predict(x)[0]
        predicted_label = np.argmax(predicted)
        return predicted_label

    def extract_training_data(self, url_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        data_size = url_data.shape[0]
        x = np.zeros((data_size, self.max_url_seq_length))
        y = np.zeros((data_size, 2))
        for i in range(data_size):
            url = url_data['url'][i]
            label = url_data['label'][i]
            for idx, ch in enumerate(url):
                x[i, idx] = self.char2idx[ch]

            y[i, label] = 1

        return x, y

    def fit(self, model: Dict, url_data: pd.DataFrame, model_dir_path: PosixPath,
            batch_size: int = 64, epochs: int = 30, test_size: float = 0.2, random_state: int = 42) -> History:
        self.n_input_tokens = model['n_input_tokens']
        self.char2idx = model['char2idx']
        self.idx2char = model['idx2char']
        self.max_url_seq_length = model['max_url_seq_length']
        self.embed_dim = model['embed_dim']

        np.save(self.get_config_path(model_dir_path), model)

        weights_file_path = self.get_weights_path(model_dir_path)
        checkpoint = ModelCheckpoint(weights_file_path)

        x, y = self.extract_training_data(url_data)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=random_state)

        self.model = make_bilstm_model(self.n_input_tokens, self.max_url_seq_length, self.embed_dim)

        with open(self.get_arch_path(model_dir_path), 'wt') as f:
            f.write(self.model.to_json())

        history = self.model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs, verbose=1,
                                 validation_data=(x_test, y_test), callbacks=[checkpoint])

        self.model.save_weights(weights_file_path)

        np.save(str(model_dir_path / (BiLstmPredictor.model_name + '-history.npy')), history.history)

        return history
