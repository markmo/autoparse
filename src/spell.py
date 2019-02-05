import hashlib
import os
import pandas as pd


class LCSObject(object):

    def __init__(self, template, ids):
        self.template = template
        self.ids = ids


class Node(object):
    """ A node in the Prefix Tree data structure """

    def __init__(self, token, count):
        self.cluster = None
        self.token = token
        self.count = count
        self.children = {}


class LogParser(object):

    def __init__(self, log_dir, filename, output_dir, log_format=None, tau=0.5, regexs=None):
        self.log_dir = log_dir
        self.filename = filename
        self.output_dir = output_dir
        self.log_format = log_format
        self.tau = tau
        self.regexs = regexs or []
        self.log_df = None

    @staticmethod
    def lcs(seq1, seq2):
        lengths = [[0 for _ in range(len(seq2) + 1)] for _ in range(len(seq1) + 1)]

        # row 0, column 0 are initialized to 0 already
        for i in range(len(seq1)):
            for j in range(len(seq2)):
                if seq1[i] == seq2[j]:
                    lengths[i + 1][j + 1] = lengths[i][j] + 1
                else:
                    lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])

        # read the substring from the matrix
        result = []
        seq1_len, seq2_len = len(seq1), len(seq2)
        while seq1_len != 0 and seq2_len != 0:
            if lengths[seq1_len][seq2_len] == lengths[seq1_len - 1][seq2_len]:
                seq1_len -= 1
            elif lengths[seq1_len][seq2_len] == lengths[seq1_len][seq2_len - 1]:
                seq2_len -= 1
            else:
                assert seq1[seq1_len] == seq2[seq2_len - 1]
                result.insert(0, seq1[seq1_len - 1])
                seq1_len -= 1
                seq2_len -= 1

        return result

    @staticmethod
    def simple_loop_match(clusters, seq):
        for cluster in clusters:
            if len(cluster.template) < (0.5 * len(seq)):
                continue

            # If the template is a subsequence of sequence s
            if all(token in seq or token == '*' for token in cluster.template):
                return cluster

        return None

    def prefix_tree_match(self, parent_node, seq, idx):
        n = len(seq)
        for i in range(idx, n):
            if seq[i] in parent_node.children:
                child_node = parent_node.children[seq[i]]
                if child_node.cluster is not None:
                    const_lm = [w for w in child_node.cluster.template if w != '*']
                    if len(const_lm) > (self.tau * n):
                        return child_node.cluster
                else:
                    return self.prefix_tree_match(child_node, seq, i + 1)

        return None

    def lcs_match(self, clusters, seq):
        cluster = None
        max_len = -1
        max_cluster = None
        seq_set = set(seq)
        n_seq = len(seq)
        for c in clusters:
            template_set = set(c.template)
            if len(seq_set & template_set) < (0.5 * n_seq):
                continue

            lcs = self.lcs(seq, c.template)
            n_lcs = len(lcs)
            if n_lcs > max_len or (n_lcs == max_len and len(c.template) < len(max_cluster.template)):
                max_len = n_lcs
                max_cluster = c

        # LCS must be greater than tau * len(self)
        if max_len >= (self.tau * n_seq):
            cluster = max_cluster

        return cluster

    @staticmethod
    def get_template(lcs, seq):
        template = []
        if not lcs:
            return template

        lcs = lcs[::-1]
        i = 0
        for token in seq:
            i += 1
            if token == lcs[-1]:
                template.append(token)
                lcs.pop()
            else:
                template.append('*')

            if not lcs:
                break

        if i < len(seq):
            template.append('*')

        return template

    @staticmethod
    def add_seq_to_prefix_tree(root_node, new_cluster):
        seq = new_cluster.template
        seq = [w for w in seq if w != '*']
        parent_node = root_node
        for i in range(len(seq)):
            token = seq[i]
            if token in parent_node.children:
                parent_node.children[token].count += 1
            else:
                parent_node.children[token] = Node(token, 1)

            parent_node = parent_node.children[token]

        if parent_node.cluster is None:
            parent_node.cluster = new_cluster

    @staticmethod
    def remove_seq_from_prefix_tree(root_node, new_cluster):
        seq = new_cluster.template
        seq = [w for w in seq if w != '*']
        parent_node = root_node
        for token in seq:
            if token in parent_node.children:
                matched_node = parent_node.children[token]
                if matched_node.template == 1:
                    del parent_node.children[token]
                    break
                else:
                    matched_node.count -= 1
                    parent_node = matched_node

    def output_result(self, clusters):
        templates = [0] * self.log_df.shape[0]
        ids = [0] * self.log_df.shape[0]
        events = []
        for cluster in clusters:
            template_str = ' '.join(cluster.template)
            event_id = hashlib.md5(template_str.encode('utf-8')).hexdigest()[0:8]
            for log_id in cluster.ids:
                templates[log_id - 1] = template_str
                ids[log_id - 1] = event_id

            events.append([event_id, template_str, len(cluster.ids)])

        event_df = pd.DataFrame(events, columns=['event_id', 'template', 'count'])
        self.log_df.assign(event_id=ids, template=templates)
        self.log_df.to_csv(os.path.join(self.output_dir, self.filename + '_structured.csv'), index=False)
        event_df.to_csv(os.path.join(self.output_dir, self.filename + '_templates.csv'), index=False)
