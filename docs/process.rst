Process
=======

1. Filter log entries from Elasticsearch using `neo23x0/sigma <https://github.com/Neo23x0/sigma>`_.

   This uses a ruleset to identify log entries of interest for further processing.
   An example rule is shown below, followed by example output

   Sigma converts rules into a back-end query. Identified log entries can be converted
   into a rule spec.

   This is done by `filter.py <../src/filter.py>`_.

::

    title: Apache Segmentation Fault
    description: Detects a segmentation fault error message caused by a crashing apache worker process
    author: Florian Roth
    references:
        - http://www.securityfocus.com/infocus/1633
    logsource:
        product: apache
    detection:
        keywords:
            - 'exit signal Segmentation Fault'
        condition: keywords
    falsepositives:
        - Unknown
    level: high

    {
      "query": {
        "constant_score": {
          "filter": {
            "multi_match": {
              "query": "exit signal Segmentation Fault",
              "fields": [],
              "type": "phrase"
            }
          }
        }
      }
    }

2. Extract templates and parameters from filtered log entries using Spell algorithm.

   Examples of log templates and extract parameters:

::

    <VERSION>: restart.
    klogd <VERSION>, log source = <PROCESS> started.
    Cannot find map file.
    No module symbols loaded - kernel modules not enabled.
    Cannot build symbol table - disabling symbol lookups
    User bal (<IP_ADDRESS>) set 'SYSLOG_INFO' to ' <IP_ADDRESS>'
    User bal (<IP_ADDRESS>) set * to *


    {
      "log_id": "46d2ef22",
      "line": "logger: User bal (192.168.139.1) set 'SYSLOG_INFO' to ' 192.168.139.1'",
      "message": "User bal (192.168.139.1) set 'SYSLOG_INFO' to ' 192.168.139.1'",
      "metadata": {
        "process": "logger"
      },
      "log_key": "User bal (<IP_ADDRESS>) set 'SYSLOG_INFO' to ' <IP_ADDRESS>'",
      "event_id": 5,
      "params": [
        {
          "start": 10,
          "end": 23,
          "entity": "ip_address",
          "value": "192.168.139.1",
          "pos": 0
        },
        {
          "start": 48,
          "end": 61,
          "entity": "ip_address",
          "value": "192.168.139.1",
          "pos": 1
        }
      ]
    }
