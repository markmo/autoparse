# autoparse

The goal is to process logs emitted from various applications and network components, 
and look for patterns that highlight a potential threat or need for further investigation.

The first step is to parse a wide variety of semi-structured logs. While a number of 
standard log formats exist, many are application specific and contain natural language 
messages that have relevant information. The time and cost to develop customer parsers 
is too high, which is a constraining factor to mine potentially relevant sources for 
information.

An automatic approach to parsing log records would open up the range of potentially 
relevant sources to identify issues within time to act.

**Extracting Message Types**

We can leverage the fact that log messages are generated from code and therefore will 
exhibit a degree a repetition and standardisation of message format. Many automatic log 
parsing approaches focus on extracting message types (aka Log Keys) and their parameters.

The log key of a log entry `e` refers to the string constant k from the print statement in 
the source code which printed e during the execution of that code. For example, the log 
key `k` for log entry `e = "Took 10 seconds to build instance."` is `k = "Took * seconds 
to build instance."`, which is the string constant from the print statement 
`printf("Took %f seconds to build instance.", t)`. Note that the parameter(s) are abstracted 
as asterisk(s) in a log key. We expect the same log key per message type.

This way, we can reduce log files to a smaller set of token structures to train a classifier on.

Values of certain parameters may serve as identifiers for a particular execution sequence, 
such as block_id in a HDFS log and instance_id in an OpenStack log. These identifiers can 
group log entries together or untangle log entries produced by concurrent processes to 
separate, single-thread sequential sequences.

We can use the values of certain parameters to lookup external information, such as whether 
an IP address has been blacklisted.

A common algorithm, with good performance, and which can be applied against a stream that 
may emit new, unseen message type, is Spell - Streaming Parser for Event Logs using an LCS.

**Spell - Streaming Parser for Event Logs using Longest Common Subsequence**

The Longest Common Subsequence (LCS) algorithm finds the longest common subsequence of 
tokens across log entries. A log message or a log record/entry refers to one line in the log 
file, which is produced by a log printing statement in the source code of a user or kernel 
program running on or inside the system.

The goal is to find message types and separate the message type template from the parameter 
values. For example, a log printing statement: `printf("Temperature %s exceeds warning threshold\n", tmp);` 
may produce several log entries such as: `"Temperature (41C) exceeds warning threshold"` 
where the parameter value is `"41C"`, and the message type is: `"Temperature * exceeds warning threshold."`

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