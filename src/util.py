from sklearn.metrics import precision_recall_fscore_support


def metrics(y_pred, y_true):
    """
    Calculate evaluation metrics for precision, recall, and F1-score

    :param y_pred: (ndarray) the predicted result array
    :param y_true: (ndarray) the ground truth label array
    :return:
        precision: (float)
        recall: (float)
        f1: (float)
    """
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    return precision, recall, f1
