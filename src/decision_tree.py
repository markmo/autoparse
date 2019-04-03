from sklearn.tree import DecisionTreeClassifier
from util import metrics


class DecisionTree(object):
    """
    Implementation of the Decision Tree Model for anomaly detection.

    References:
        [1] Mike Chen, Alice X. Zheng, Jim Lloyd, Michael I. Jordan, Eric Brewer.
            Failure Diagnosis Using Decision Trees. IEEE International Conference
            on Autonomic Computing (ICAC), 2004.
    """
    def __init__(self, criterion='gini', max_depth=None, max_features=None, class_weight=None):
        self.classifier = DecisionTreeClassifier(criterion=criterion, max_depth=max_depth,
                                                 max_features=max_features, class_weight=class_weight)

    def fit(self, x, y):
        """

        :param x: (ndarray) the event count matrix, shape [n_instances, n_events]
        :param y:
        :return:
        """
        self.classifier.fit(x, y)

    def predict(self, x):
        """
        Predict anomalies

        :param x: the input event count matrix
        :return: y_pred: (ndarray) the predicted label vector, shape [n_instances, ]
        """
        return list(self.classifier.predict(x))

    def evaluate(self, x, y_true):
        y_pred = self.predict(x)
        precision, recall, f1 = metrics(y_pred, y_true)
        print('Precision: {:.3f}, Recall: {:.3f}, F1-score: {:.3f}\n'.format(precision, recall, f1))
        return precision, recall, f1
