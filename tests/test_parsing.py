import pytest
import spacy

from config import REGEXS
from pyspell.spell_stream import LCSMap, preprocess


@pytest.fixture
def nlp():
    return spacy.load('en_core_web_sm')


def test_preprocessing():
    line = "User bal (192.168.139.1) set 'SYSLOG_NOTICE' to ''"
    result, params = preprocess(line, REGEXS)
    assert len(params) == 1
    assert params[0][3] == 'ip_address'  # entity type
    assert params[0][0] == 10  # char_start
    assert params[0][1] == 23  # char_end
    assert params[0][2] == '192.168.139.1'  # entity value
    repl = '<IP_ADDRESS>'
    assert result[10:(10 + len(repl))] == repl


def test_nlp(nlp):
    line = 'Donald Trump gives himself a gold star'
    doc = nlp(line)
    ent = doc.ents[0]
    assert ent.label_ == 'PERSON'
    assert ent.text == 'Donald Trump'
    assert ent.start == 0
    assert ent.end == 2


def test_lcs():
    lines = [
        "1.4.1: restart.",
        "Cannot build symbol table - disabling symbol lookups",
        "User bal (192.168.139.1) set 'SYSLOG_NOTICE' to ''",
        "User bal (192.168.139.2) set 'SYSLOG_WARN' to ''",
        "User bal (192.168.139.3) set 'SYSLOG_ERR' to ''"
    ]
    slm = LCSMap(r'\s+')
    obj, params = None, None
    for line in lines:
        obj = slm.insert(line)
        params = obj.param(line)

    log_key = obj.lcsseq()
    assert log_key == "User bal * set * to ''"
    assert params[0][0][1] == '(192.168.139.3)'  # entity value
    assert params[1][0][1] == "'SYSLOG_ERR'"  # entity value
    assert params[1][0][0] == 4  # token start position
