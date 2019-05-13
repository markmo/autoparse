Extracting Message Types
========================

We can leverage the fact that log messages are generated from code and therefore will
exhibit a degree a repetition and standardisation of message format. Many automatic log
parsing approaches focus on extracting message types (aka Log Keys) and their parameters.

The log key of a log entry ``e`` refers to the string constant k from the print statement in
the source code which printed e during the execution of that code. For example, the log
key ``k`` for log entry ``e = "Took 10 seconds to build instance."`` is ``k = "Took * seconds
to build instance."``, which is the string constant from the print statement
``printf("Took %f seconds to build instance.", t)``. Note that the parameter(s) are abstracted
as asterisk(s) in a log key. We expect the same log key per message type.

This way, we can reduce log files to a smaller set of token structures to train a classifier on.

Values of certain parameters may serve as identifiers for a particular execution sequence,
such as block_id in a HDFS log and instance_id in an OpenStack log. These identifiers can
group log entries together or untangle log entries produced by concurrent processes to
separate, single-thread sequential sequences.

We can use the values of certain parameters to lookup external information, such as whether
an IP address has been blacklisted.

A common algorithm, with good performance, and which can be applied against a stream that
may emit new, unseen message type, is *Spell - Streaming Parser for Event Logs using an LCS.*
