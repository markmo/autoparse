Model to predict malicious URLs
===============================

Starting with the simplest example I could think of (due to availability of a training set), we will
score URLs found from logs on likelihood of being an address to a phishing or otherwise malicious
site. We will train a Deep Learning model for this purpose, based on comparative benchmarks of
performance from a literature search.

This model uses a `Bidirectional LSTM <https://en.wikipedia.org/wiki/Bidirectional_recurrent_neural_networks>`_.

See `Understanding LSTM Networks <https://colah.github.io/posts/2015-08-Understanding-LSTMs/>`_
for a primer on LSTM (Long Short-Term Memory) Networks.