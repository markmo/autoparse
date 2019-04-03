from itertools import combinations
import numpy as np
from util import metrics


class InvariantsMiner(object):
    """
    Implementation of the Invariants Mining Model for anomaly detection.

    Reference:
        [1] Jian-Guang Lou, Qiang Fu, Shengqi Yang, Ye Xu, Jiang Li. Mining Invariants
            from Console Logs for System Problem Detection. USENIX Annual Technical
            Conference (ATC), 2010.
    """
    def __init__(self, percentage=0.98, epsilon=0.5, longest_invariant=None, scale_list=None):
        """

        :param percentage: (float) percentage of samples satisfying the condition that |X_j * V_i| < epsilon
        :param epsilon: (float) threshold for estimating the invariant space
        :param longest_invariant: (int) maximum length of the invariant. Default is None.
               Stop searching when the invariant length is greater than this argument.
        :param scale_list: (list) used to scale theta of float into integer
        """
        if scale_list is None:
            scale_list = [1, 2, 3]

        self.percentage = percentage
        self.epsilon = epsilon
        self.longest_invariant = longest_invariant
        self.scale_list = scale_list

        # dictionary of invariants where key is the selected columns and value is the
        # weights of the invariant
        self.invariants = None

    def fit(self, x):
        """

        :param x: (ndarray) the event count matrix, shape [n_instances, n_events]
        :return:
        """
        invar_dim = self._estimate_invariant_space(x)
        self._invariants_search(x, invar_dim)

    def predict(self, x):
        """
        Predicts anomalies with mined invariants

        :param x: (ndarray) the input event count matrix
        :return: y_pred: (ndarray) the predicted label vector, shape [n_instances, ]
        """
        y_sum = np.zeros(x.shape[0])
        for cols, theta in self.invariants.items():
            y_sum += np.fabs(np.dot(x[:, cols], np.array(theta)))

        return (y_sum > 1e-6).astype(int)

    def evaluate(self, x, y_true):
        print('-------- Evaluation summary --------')
        y_pred = self.predict(x)
        precision, recall, f1 = metrics(y_pred, y_true)
        print('Precision: {:.3f}, Recall: {:.3f}, F1-score: {:.3f}\n'.format(precision, recall, f1))
        return precision, recall, f1

    def _estimate_invariant_space(self, x):
        """
        Estimate the dimension of invariant space using SVD decomposition

        :param x: (ndarray) the event count matrix, shape [n_instances, n_events]
        :return: r: dimension of invariant space
        """
        covariance_mat = np.dot(x.T, x)
        u, sigma, v = np.linalg.svd(covariance_mat)  # SVD decomposition

        # start from the right-most column of matrix V
        # singular values are in ascending order
        n_instances, n_events = x.shape
        r = 0
        for i in range(n_events - 1, -1, -1):
            zero_count = sum(abs(np.dot(x, u[:, i])) < self.epsilon)
            if zero_count / float(n_instances) < self.percentage:
                break

            r += 1

        print('Invariant space dimension: {}'.format(r))
        return r

    def _invariants_search(self, x, r):
        """
        Mine invariant relationships from X

        :param x: (ndarray) the event count matrix, shape [n_instances, n_events]
        :param r: dimension of invariant space
        :return:
        """
        n_instances, n_events = x.shape
        invariants = {}  # save the mined invariants (value) and its corresponding columns (key)
        search_space = []  # only invariant candidates in this list are valid

        # invariant of only one column (all zero columns)
        init_cols = [[x] for x in range(n_events)]
        for col in init_cols:
            search_space.append(col)

        init_col_list = init_cols[:]
        for col in init_cols:
            if np.count_nonzero(x[:, col]) == 0:
                invariants[tuple(col)] = [1]
                search_space.remove(col)
                init_col_list.remove(col)

        item_list = init_col_list
        length = 2
        break_loop_flag = False

        # check invariant of more columns
        while len(item_list) != 0:
            if self.longest_invariant and len(item_list[0]) >= self.longest_invariant:
                break

            joined_item_list = self._join_set(item_list, length)  # generate new invariant candidates
            for items in joined_item_list:
                if self._check_valid_candidates(items, length, search_space):
                    search_space.append(items)

            item_list = []
            for item in joined_item_list:
                if tuple(item) in invariants:
                    continue

                if item not in search_space:
                    continue

                # an item must be a superset of all other sub-items in search_space, else skip
                if not self._check_valid_candidates(tuple(item), length, search_space) and length > 2:
                    search_space.remove(item)
                    continue

                validity, scaled_theta = self._check_invar_validity(x, item)
                if validity:
                    self._prune(invariants.keys(), set(item), search_space)
                    invariants[tuple(item)] = scaled_theta.tolist()
                    search_space.remove(item)
                else:
                    item_list.append(item)

                if len(invariants) >= r:
                    break_loop_flag = True
                    break

            if break_loop_flag:
                break

            length += 1

        print('Mined {} invariants: {}\n'.format(len(invariants), invariants))
        self.invariants = invariants

    @staticmethod
    def _compute_eigenvector(x):
        """
        Calculate the smallest eigenvalue and corresponding eigenvector (theta in paper)
        for a given sub-matrix

        :param x: the event count matrix (each row is a log sequence vector, each column
               represents an event)
        :return:
            min_vec: the eigenvector of the corresponding minimum eigen value
            contain_zero_flag: whether min_vec contains zero (very small value)
        """
        contain_zero_flag = False
        dot_result = np.dot(x.T, x)
        u, s, v = np.linalg.svd(dot_result)
        min_vec = u[:, -1]
        count_zero = sum(np.fabs(min_vec) < 1e-6)
        if count_zero != 0:
            contain_zero_flag = True

        return min_vec, contain_zero_flag

    def _check_invar_validity(self, x, selected_columns):
        """
        Scale the eigenvector of float into integer and check whether the scaled
        number is valid

        :param x: the event count matrix (each row is a log sequence vector;
               each column represents an event)
        :param selected_columns: select columns from column list
        :return:
            validity: whether the selected columns are valid
            scaled_theta: the scaled theta vector
        """
        sub_matrix = x[:, selected_columns]
        inst_num = x.shape[0]
        validity = False
        scaled_theta = None
        min_theta, contain_zero_flag = self._compute_eigenvector(sub_matrix)
        abs_min_theta = [np.fabs(x) for x in min_theta]
        if contain_zero_flag:
            return validity, []
        else:
            for i in self.scale_list:
                min_index = np.argmin(abs_min_theta)
                scale = float(i) / min_theta[min_index]
                scaled_theta = np.array([round(x * scale) for x in min_theta])
                scaled_theta[min_index] = i
                scaled_theta = scaled_theta.T
                if 0 in np.fabs(scaled_theta):
                    continue

                dot_submat_theta = np.dot(sub_matrix, scaled_theta)
                count_zero = 0
                for j in dot_submat_theta:
                    if np.fabs(j) < 1e-8:
                        count_zero += 1

                if count_zero >= self.percentage * inst_num:
                    validity = True
                    # print('A valid invariant is found:', scaled_theta, selected_columns)
                    break

            return validity, scaled_theta

    @staticmethod
    def _prune(valid_cols, new_item_set, search_space):
        """
        Prune invalid combinations of columns

        :param valid_cols: existing valid column list
        :param new_item_set: item set to be merged
        :param search_space: the search space that stores possible candidates
        :return:
        """
        if len(valid_cols) == 0:
            return

        for se in valid_cols:
            intersection = set(se) & new_item_set
            if len(intersection) == 0:
                continue

            union = set(se) | new_item_set
            for it in list(intersection):
                diff = sorted(list(union - {it}))
                if diff in search_space:
                    search_space.remove(diff)

    @staticmethod
    def _join_set(item_list, length):
        """
        Join a set with itself and return the n-element (length) itemsets

        :param item_list: current list of columns
        :param length: generate new items of length
        :return: return_list: list of items of length-element
        """
        set_len = len(item_list)
        return_list = []
        for i in range(set_len):
            for j in range(i + 1, set_len):
                i_set = set(item_list[i])
                j_set = set(item_list[j])
                if len(i_set.union(j_set)) == length:
                    joined = sorted(list(i_set.union(j_set)))
                    if joined not in return_list:
                        return_list.append(joined)

        return sorted(return_list)

    @staticmethod
    def _check_valid_candidates(item, length, search_space):
        """
        Check if an item's sub-items are in `search_space`

        :param item: item to be checked
        :param length: length of item
        :param search_space: the search space that holds possible candidates
        :return: (bool)
        """
        for sub_item in combinations(item, length - 1):
            if sorted(list(sub_item)) not in search_space:
                return False

        return True
