# noinspection SpellCheckingInspection
"""
BSD 3-Clause License

Copyright (c) 2018, inoue.tomoya
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
import iocextract
import json
import pickle
import re


# noinspection SpellCheckingInspection
class LCSObject(object):

    def __init__(self, objid, seq, lineid, refmt):
        self._refmt = refmt
        if isinstance(seq, str):
            self._lcsseq = re.split(refmt, seq.strip())
        else:
            self._lcsseq = seq

        self._lineids = [lineid]
        self._pos = []
        self._sep = ' '
        self._objid = objid

    def getlcs(self, seq):
        if isinstance(seq, str):
            seq = re.split(self._refmt, seq.strip())

        count = 0
        lastmatch = -1
        for i in range(len(self._lcsseq)):
            if self._ispos(i):
                continue

            for j in range(lastmatch + 1, len(seq)):
                if self._lcsseq[i] == seq[j]:
                    lastmatch = j
                    count += 1
                    break

        return count

    def insert(self, seq, lineid):
        if isinstance(seq, str):
            seq = re.split(self._refmt, seq.strip())

        self._lineids.append(lineid)
        temp = ''
        lastmatch = -1
        placeholder = False
        for i in range(len(self._lcsseq)):
            if self._ispos(i):
                if not placeholder:
                    temp += '* '

                placeholder = True
                continue

            for j in range(lastmatch + 1, len(seq)):
                if self._lcsseq[i] == seq[j]:
                    placeholder = False
                    temp += self._lcsseq[i] + ' '
                    lastmatch = j
                    break
                elif not placeholder:
                    temp += '* '
                    placeholder = True

        temp = temp.strip()
        self._lcsseq = re.split(self._refmt, temp)
        self._pos = self._getpos()
        self._sep = self._getsep()

    def lcsseq(self):
        return ' '.join(self._lcsseq)

    def tojson(self):
        return json.dumps({
            'lcsseq': ' '.join(self._lcsseq),
            'lineids': self._lineids,
            'position': self._pos
        })

    def __len__(self):
        return len(self._lcsseq)

    def param(self, seq):
        if isinstance(seq, str):
            seq = re.split(self._refmt, seq.strip())

        j = 0
        ret = []
        prev_token = None
        fill_next_token = False
        for i in range(len(self._lcsseq)):
            slot = []
            if self._ispos(i):
                while j < len(seq):
                    if i != (len(self._lcsseq) - 1) and self._lcsseq[i + 1] == seq[j]:
                        break
                    else:
                        slot.append([j, seq[j], prev_token, None])
                        fill_next_token = True
                        prev_token = None

                    j += 1

                ret.append(slot)
            elif self._lcsseq[i] != seq[j]:
                return []
            else:
                prev_token = self._lcsseq[i]
                if fill_next_token:
                    if slot:
                        slot[-1][3] = prev_token

                    if ret:
                        ret[-1][-1][3] = prev_token

                fill_next_token = False
                j += 1

        if j != len(seq):
            return []

        return ret

    def reparam(self, seq):
        if isinstance(seq, list):
            seq = ' '.join(seq)

        seq = seq.strip()
        ret = []
        print(self._sep)
        print(seq)
        p = re.split(self._sep, seq)
        for i in p:
            if len(i) != 0:
                ret.append(re.split(self._refmt, i.strip()))

        if len(ret) == len(self._pos):
            return ret

        return None

    def _ispos(self, idx):
        for i in self._pos:
            if i == idx:
                return True

        return False

    @staticmethod
    def _tcat(seq, s, e):
        sub = ''
        for i in range(s, e + 1):
            sub += seq[i] + ' '

        return sub.rstrip()

    def _getsep(self):
        sep_token = []
        s, e = 0, 0
        for i in range(len(self._lcsseq)):
            if self._ispos(i):
                if s != e:
                    sep_token.append(self._tcat(self._lcsseq, s, e))

                s = i + 1
                e = s
            else:
                e = i

            if e == len(self._lcsseq) - 1:
                sep_token.append(self._tcat(self._lcsseq, s, e))
                break

        ret = ''
        for i in range(len(sep_token)):
            if i == len(sep_token) - 1:
                ret += sep_token[i]
            else:
                ret += sep_token[i] + '|'

        return ret

    def _getpos(self):
        pos = []
        for i in range(len(self._lcsseq)):
            if self._lcsseq[i] == '*':
                pos.append(i)

        return pos

    def getobjid(self):
        return self._objid


# noinspection SpellCheckingInspection
class LCSMap(object):

    def __init__(self, refmt):
        self._refmt = refmt
        self._lcsobjs = []
        self._lineid = 0
        self._objid = 0

    def insert(self, entry):
        seq = re.split(self._refmt, entry.strip())
        obj = self.match(seq)
        if obj is None:
            self._lineid += 1
            obj = LCSObject(self._objid, seq, self._lineid, self._refmt)
            self._lcsobjs.append(obj)
            self._objid += 1
        else:
            self._lineid += 1
            obj.insert(seq, self._lineid)

        return obj

    def match(self, seq):
        if isinstance(seq, str):
            seq = re.split(self._refmt, seq.strip())

        bestmatch = None
        bestmatch_len = 0
        seqlen = len(seq)
        for obj in self._lcsobjs:
            objlen = len(obj)
            if objlen < (seqlen / 2) or objlen > (seqlen * 2):
                continue

            lcs = obj.getlcs(seq)
            if lcs >= (seqlen / 2) and lcs > bestmatch_len:
                bestmatch = obj
                bestmatch_len = lcs

        return bestmatch

    def __getitem__(self, idx):
        return self._lcsobjs[idx]

    def __len__(self):
        return len(self._lcsobjs)

    def __dir__(self):
        for i in self._lcsobjs:
            print(i.tojson())


# noinspection SpellCheckingInspection
def save(filename, lcsmap):
    if type(lcsmap) == LCSMap:
        with open(filename, 'wb') as f:
            pickle.dump(lcsmap, f)
    else:
        if __debug__ is True:
            print('%s isn\'t slm object' % filename)


def load(filename):
    with open(filename, 'rb') as f:
        slm = pickle.load(f)
        if type(slm) == LCSMap:
            return slm

        if __debug__ is True:
            print('%s isn\'t slm object' % filename)

        return None


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


def get_ioc_param(ioc_type, ioc, line):
    char_start = line.find(ioc)
    char_end = char_start + len(ioc)
    token_start = len(re.split(r'\s+', line[:char_start])) - 1
    token_end = token_start + 1
    return [char_start, char_end, ioc, ioc_type, token_start, token_end]


def ioc_parse(line):
    """ Use library that can handle defanged formats for IOCs (Indicators of Compromise) """
    params = []
    formatted = line
    for url in iocextract.extract_urls(formatted, strip=True):
        refanged = iocextract.refang_url(url)
        param = get_ioc_param('url', url, formatted)
        param.append(refanged)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], url, formatted[param[1]:])

    for ip in iocextract.extract_ipv4s(formatted):
        refanged = iocextract.refang_ipv4(ip)
        param = get_ioc_param('ip_address', ip, formatted)
        param.append(refanged)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], ip, formatted[param[1]:])

    for ip in iocextract.extract_ipv6s(formatted):
        param = get_ioc_param('ip_address', ip, formatted)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], ip, formatted[param[1]:])

    for email in iocextract.extract_emails(formatted):
        refanged = iocextract.refang_email(email)
        param = get_ioc_param('email', email, formatted)
        param.append(refanged)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], email, formatted[param[1]:])

    for h in iocextract.extract_hashes(formatted):
        param = get_ioc_param('hash', h, formatted)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], h, formatted[param[1]:])

    for rule in iocextract.extract_yara_rules(formatted):
        param = get_ioc_param('yara_rule', rule, formatted)
        params.append(param)
        formatted = '{}<{}>{}'.format(formatted[:param[0]], rule, formatted[param[1]:])

    return formatted, params


def preprocess(line, regexs):
    params = []
    formatted = line
    for entity, regex in regexs.items():
        # convert to list so we can see if empty without consuming the iterator
        matches = list(re.finditer(regex, formatted))

        # more efficient version
        for match in matches:
            start, end = match.start(), match.end()
            formatted = '{}<{}>{}'.format(formatted[:start], entity.upper(), formatted[end:])
            token_start = len(line[:start].split())
            params.append([start, end, match.group(0), entity, token_start, token_start + 1])
        # if not_empty(matches):
        #     formatted = re.sub(regex, '<{}>'.format(entity.upper()), line)
        #     for match in matches:
        #         token_start = len(line[:match.start()].split())
        #         params.append([match.start(), match.end(), match.group(0), entity, token_start, token_start + 1])

    return formatted, params


def is_empty(collection: list) -> bool:
    return len(collection) == 0


def not_empty(collection: list) -> bool:
    return len(collection) > 0


def get_span(seq, idx):
    start = 0
    for i, t in enumerate(seq):
        if i == idx:
            return start, start + len(t)

        start += len(t) + 1

    return None
