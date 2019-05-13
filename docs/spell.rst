Spell (Streaming Parser for Event Logs using Longest Common Subsequence)
========================================================================

The Longest Common Subsequence (LCS) algorithm finds the longest common subsequence of
tokens across log entries. A log message or a log record/entry refers to one line in the log
file, which is produced by a log printing statement in the source code of a user or kernel
program running on or inside the system.

The goal is to find message types and separate the message type template from the parameter
values. For example, a log printing statement: ``printf("Temperature %s exceeds warning threshold\n", tmp);``
may produce several log entries such as: ``"Temperature (41C) exceeds warning threshold"``
where the parameter value is ``"41C"``, and the message type is: ``"Temperature * exceeds warning threshold."``

A structured log parser is to parse log and produce all message types from those m statements.
The key observation is that, if we view the output by a log printing statement (which is a
log entry) as a sequence, in most log printing statements, the constant that represents a
message type often takes a majority part of the sequence and the parameter values take only
a small portion.

If two log entries are produced by the same log printing statement stat, but only differ by
having different parameter values, the LCS of the two sequences is very likely to be the
constant in the code stat, implying a message type.

Spell was designed for a streaming use case, i.e. the LCS sequence of two log messages is
naturally a message type, which makes streaming log parsing possible.

From Spell, we can derive message templates. We train a model to classify which templates
are relevant, then use the template as part of a regex to extract structured information.

See `this paper <https://www.cs.utah.edu/~lifeifei/papers/spell.pdf>`_ for more information.

Spell, given for example Kemp logs, will produce structure output as follows:

Sample input:

::

    logger: User bal Timed out (Session : ad512a526c4e19642)
    stats: VSstatus: 0 Total, 0 Up 0 Down 0 Disabled
    stats: RSstatus: 0 Total, 0 Up 0 Down 0 Disabled
    stats: SubVSstatus: 0 Total, 0 Up 0 Down 0 Disabled
    login[25288]: pam_unix(login:auth): check pass; user unknown
    login[25288]: pam_unix(login:auth): authentication failure; logname=LOGIN uid=0 euid=0 tty=/dev/tty1 ruser= rhost=
    login[25288]: FAILED LOGIN (1) on '/dev/tty1' FOR 'UNKNOWN', Authentication failure

Structured output:

::

    LineId,Process,Content,EventId,EventTemplate,Parameters
    20,logger,User bal Timed out (Session : ad512a526c4e19642),b72d970b,User <*> Timed out (Session : <*>,"[""bal"",""ad512a526c4e19642""]"
    21,stats,"VSstatus: 0 Total, 0 Up 0 Down 0 Disabled",dc8c71e4,"VSstatus: <*> Total, <*> Up <*> Down 0 Disabled","[0,0,0]"
    22,stats,"RSstatus: 0 Total, 0 Up 0 Down 0 Disabled",a3b39f5c,"RSstatus: <*> Total, <*> Up <*> Down 0 Disabled","[0,0,0]"
    23,stats,"SubVSstatus: 0 Total, 0 Up 0 Down 0 Disabled",3f401b6e,"SubVSstatus: 0 Total, 0 Up 0 Down 0 Disabled","[0,0,0]"
    24,login[25288],pam_unix(login:auth): check pass; user unknown,cc6f52d7,pam_unix(login:auth): check pass; user unknown,"[]"
    25,login[25288],pam_unix(login:auth): authentication failure; logname=LOGIN uid=0 euid=0 tty=/dev/tty1 ruser= rhost=,88abdb22,pam_unix(login:auth): authentication failure; logname=LOGIN uid=0 euid=0 tty=<*> ruser= rhost=,"[""/dev/tty1""]"
    26,login[25288],"FAILED LOGIN (1) on '/dev/tty1' FOR 'UNKNOWN', Authentication failure",83a09411,"FAILED LOGIN (1) on '<*>' FOR 'UNKNOWN', Authentication failure","[1]"

Event templates:

::

    EventId,EventTemplate,Occurrences
    b72d970b,User <*> Timed out (Session : <*>,11
    dc8c71e4,"VSstatus: <*> Total, <*> Up <*> Down 0 Disabled",14
    a3b39f5c,"RSstatus: <*> Total, <*> Up <*> Down 0 Disabled",13
    3f401b6e,"SubVSstatus: 0 Total, 0 Up 0 Down 0 Disabled",10
    cc6f52d7,pam_unix(login:auth): check pass; user unknown,2
    88abdb22,pam_unix(login:auth): authentication failure; logname=LOGIN uid=0 euid=0 tty=<*> ruser= rhost=,2
    83a09411,"FAILED LOGIN (1) on '<*>' FOR 'UNKNOWN', Authentication failure",2


The set of event templates will be much smaller than the set of log records. We can apply
NER against the set of event templates, construct a knowledge graph of entity, referenced
to template (event_id) and log record (log_id), and reference lookup information for
parameter values (e.g. whether an IP address appears in a blacklist site).

Given the performance (and cost) overhead of looking up information with external services,
the lookups will be delayed. A downstream analytic process will flag clusters of interest and
perform lookups for only those nodes.

TODO: From initial tests, Spell works pretty well out of the box. However, I'm getting slightly
better results from a paper published the following year (2017) - Drain.

See Drain: An Online Log Parsing Approach with Fixed Depth Tree, Proceedings of the 24th
International Conference on Web Services (ICWS), 2017. (http://jmzhu.logpai.com/pub/pjhe_icws2017.pdf)
