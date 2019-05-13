from datetime import datetime
import hashlib
import json
import os
import pandas as pd
import re


class LCSObject(object):

    def __init__(self, template, log_ids):
        self.template = template
        self.log_ids = log_ids


class Node(object):
    """ A node in the Prefix Tree data structure """

    def __init__(self, token='', count=0):
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
                assert seq1[seq1_len - 1] == seq2[seq2_len - 1]
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
        params = []
        template = []
        if not lcs:
            return template

        lcs = lcs[::-1]
        i = 0
        pos = 0
        for token in seq:
            i += 1
            if token == lcs[-1]:
                template.append(token)
                lcs.pop()
            else:
                template.append('*')
                params.append([pos, pos + len(token), token, None])

            pos += len(token) + 1
            if not lcs:
                break

        if i < len(seq):
            template.append('*')
            t = ' '.join(seq[i:])
            params.append([pos, pos + len(t), t, None])

        return template, params

    @staticmethod
    def get_parameters(lcs, seq, original_seq):
        params = []
        if not lcs:
            return params

        lcs = lcs[::-1]
        i = 0
        pos = 0
        for token in seq:
            i += 1
            if token != lcs[-1]:
                params.append([pos, pos + len(token), token, None])

            lcs.pop()
            pos += len(original_seq[i - 1]) + 1
            if not lcs:
                break

        if i < len(seq):
            t = ' '.join(seq[i:])
            params.append([pos, pos + len(t), t, None])

        return params

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
                if matched_node.count == 1:
                    del parent_node.children[token]
                    break
                else:
                    matched_node.count -= 1
                    parent_node = matched_node

    def output_result(self, clusters, parameters):
        templates = [0] * self.log_df.shape[0]
        log_ids = [0] * self.log_df.shape[0]
        params = [[]] * self.log_df.shape[0]
        events = []
        for cluster in clusters:
            template_str = ' '.join(cluster.template)
            event_id = hashlib.md5(template_str.encode('utf-8')).hexdigest()[0:8]
            for log_id in cluster.log_ids:
                templates[log_id - 1] = template_str
                log_ids[log_id - 1] = event_id
                params[log_id - 1] = parameters[log_id]

            events.append([event_id, template_str, len(cluster.log_ids)])

        event_df = pd.DataFrame(events, columns=['event_id', 'template', 'count'])
        self.log_df['event_id'] = log_ids
        self.log_df['template'] = templates
        self.log_df['parameters'] = params
        self.log_df.to_csv(os.path.join(self.output_dir, self.filename + '_structured.csv'), index=False)
        event_df.to_csv(os.path.join(self.output_dir, self.filename + '_templates.csv'), index=False)

    def print_tree(self, node, depth):
        output = '\t' * depth
        if node.token == '':
            output += 'Root'
        else:
            output += node.token
            if node.cluster is not None:
                output += '-->' + ' '.join(node.cluster.template)

        print(output + ' (' + str(node.count) + ')')
        for child in node.childre:
            self.print_tree(node.children[child], depth + 1)

    def parse(self, filename):
        start_time = datetime.now()
        print('Parsing file: ' + os.path.join(self.log_dir, filename))
        self.filename = filename
        self.load_data()
        root_node = Node()
        clusters = []
        count = 0
        parameters = {}
        for i, line in self.log_df.iterrows():
            log_id = line['log_id']
            processed, params = self.preprocess(line['content'])
            ps = []
            for p in params:
                ps.append({'start': p[0], 'end': p[1], 'entity': p[3], 'value': p[2]})

            original_seq = list(filter(lambda x: x != '', re.split(r'[\s=:,]', line['content'])))
            tokens = list(filter(lambda x: x != '', re.split(r'[\s=:,]', processed)))
            const_tokens = [w for w in tokens if w != '*']

            # Find an existing matched cluster
            matched_cluster = self.prefix_tree_match(root_node, const_tokens, 0)
            if matched_cluster is None:
                matched_cluster = self.simple_loop_match(clusters, const_tokens)
                if matched_cluster is None:
                    matched_cluster = self.lcs_match(clusters, tokens)

                    # Match no existing cluster
                    if matched_cluster is None:
                        new_cluster = LCSObject(tokens, [log_id])
                        clusters.append(new_cluster)
                        self.add_seq_to_prefix_tree(root_node, new_cluster)
                    else:
                        # Add the new log message to the existing cluster
                        new_template, params = self.get_template(self.lcs(tokens, matched_cluster.template),
                                                                 matched_cluster.template)
                        if ' '.join(new_template) != ' '.join(matched_cluster.template):
                            self.remove_seq_from_prefix_tree(root_node, matched_cluster)
                            matched_cluster.template = new_template
                            self.add_seq_to_prefix_tree(root_node, matched_cluster)

            ps.sort(key=lambda x: x['start'])
            for j, p in enumerate(ps):
                p['pos'] = j

            if matched_cluster:
                matched_cluster.log_ids.append(log_id)
                params = self.get_parameters(matched_cluster.template, tokens, original_seq)
                for p in params:
                    ps.append({'start': p[0], 'end': p[1], 'entity': p[3], 'value': p[2]})

            parameters[log_id] = json.dumps(ps)

            count += 1
            if count % 1000 == 0 or count == len(self.log_df):
                print('Processed {0:.1f}% of log lines.'.format(count * 100. / len(self.log_df)))

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        self.output_result(clusters, parameters)
        print('Parsing done. [Time taken: {!s}]'.format(datetime.now() - start_time))

    def load_data(self):
        columns, regex = self.make_log_format_regex(self.log_format)
        self.log_df = self.log_to_dataframe(os.path.join(self.log_dir, self.filename), regex, columns)

    def preprocess(self, line):
        params = []
        for entity, regex in self.regexs.items():
            matches = re.finditer(regex, line)
            if matches:
                line = re.sub(regex, '*', line)
                for match in matches:
                    params.append([match.start(), match.end(), match.group(0), entity])

        return line, params

    @staticmethod
    def log_to_dataframe(filename, regex, columns):
        """ Transform log file to dataframe """
        messages = []
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                line = re.sub(r'[^\x00-\x7F]+', '<NASCII>', line)
                # noinspection PyBroadException
                try:
                    match = regex.search(line.strip())
                    message = [match.group(column) for column in columns]
                    messages.append(message)
                    count += 1
                except Exception:
                    pass

        log_df = pd.DataFrame(messages, columns=columns)
        log_df.insert(0, 'log_id', None)
        log_df['log_id'] = [i + 1 for i in range(count)]
        return log_df

    @staticmethod
    def make_log_format_regex(log_format):
        """ Make regular expression to split log messages """
        columns = []
        splitters = re.split(r'(<[^<>]+>)', log_format)
        regex = ''
        for i in range(len(splitters)):
            if i % 2 == 0:
                splitter = re.sub(' +', r'\s+', splitters[i])
                regex += splitter
            else:
                column = splitters[i].strip('<').strip('>')
                regex += '(?P<%s>.*?)' % column
                columns.append(column)

        regex = re.compile('^' + regex + '$')
        return columns, regex
