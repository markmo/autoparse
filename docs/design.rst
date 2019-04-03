Design Candidates
=================

The goal is to process logs emitted from various applications and network components,
and look for patterns that highlight a potential threat or need for further investigation.

The first step is to parse a wide variety of semi-structured logs. While a number of
standard log formats exist, many are application specific and contain natural language
messages that have relevant information. The time and cost to develop customer parsers
is too high, which is a constraining factor to mine potentially relevant sources for
information.

An automatic approach to parsing log records would open up the range of potentially
relevant sources to identify issues within time to act.

1. Applying Natural Language Processing (NLP)
---------------------------------------------

NLP has successfully been used to extract structured data from semi-structured documents
for further analysis in applications such as information retrieval, question answering,
and machine translation. There is degree of equivalence between a log file and a document.
Log records (lines of text) form sentences, which comprise tokens as words and punctuation,
or as characters. There are inherent syntax rules and grammars in the "print" statements of
each record (event) type, which can be learned using features such as position of a token
in a sequence, key terms, case, etc.

The general approach is to use Named Entity Recognition (NER) and Relation Extraction.

Named Entity Recognition
^^^^^^^^^^^^^^^^^^^^^^^^

Named Entity Recognition (NER) is a supervised approach to learn which tokens from the input
text are part of an entity of a specific type. The training set (and output) looks something like this:

::

    1
    kernel B-process
    : O
    klogd B-app
    1.4.1 B-version
    , O
    log O
    source O
    = O
    /proc/kmsg B-file
    started B-event
    . O

The input has a labelled token per line. The label is one of: O (outside of, i.e. not an entity),
B-<entity_type> (beginning of entity of a given type), I-<entity_type> (inside, i.e. continuation
of an entity). This training data is used to train a model to predict the appropriate label for
each input token. A sentence/record starts with an identifier (unlabelled), and are separated by
an empty line.

The modelling technique employed is typically:

* Conditional Random Fields (CRF);
* A Recurrent Neural Network (RNN) such as Long Short-Term Memory (LSTM) or a Bidirectional LSTM; or
* A combined BiLSTM and CRF

See https://github.com/markmo/dltemplate/tree/master/src/tf_model/bi_lstm_crf_ner for an
implementation of the latter in TensorFlow, and as described in this paper: http://www.aclweb.org/anthology/P15-1109.

The benefit of combining a Bi-LSTM and CRF is that it uses the LSTM for feature engineering,
and a CRF to apply constraints, and make use of context, e.g. previous work and next word, in
the tagging decision as well as in determining the tag score.

When dealing with textual data you need to find a way to convert text to numbers. A common
approach is to use embeddings like word2vec or Glove.

CRFs make use of human-defined features such as TF-IDF score, previous token, next token,
n-grams, case, part-of-speech (POS) tag, etc.

State-of-the-art techniques use Transformer networks and pre-trained embeddings from massive corpora.

Given the specialised tokens used in system logs versus the human language used in documents
such as twitter posts, embeddings trained on corpora such as news feeds or Wikipedia may be
less effective. It is possible to fine-tune the embeddings on the domain-specific corpus if
sufficiently labelled records exist.

It is probably worthwhile baselining results against a simple CRF model using standard features.
An out-of-the-box model such as from Spacy or Stanford NLP libraries is unlikely to perform given
the specialised terms.

Pre-processing Step
^^^^^^^^^^^^^^^^^^^

The challenge with directly applying NER to the data is the amount of human labelling required
to create the training set. With a decent sized set (thousands of labelled records), I expect
the performance to be pretty good given comparable published results.

The question is: is there any technique we can use before investing in a large manual labelling
effort? Two techniques are relevant:

1. Data Programming - using code/rules such as regular expressions to create weak labels that
   are "weighted" using a model trained on a smaller set of human (gold) labels. This solves the
   above problem by augmenting a smaller number of human labels (and therefore smaller effort)
   with a larger number of automatically generated labels. Machine learning is used to "ensemble"
   a set of weak labels to generate a large set of strong labels (closer to human annotation).
2. Extract message types from log files before applying NER.
