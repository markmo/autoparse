The Spell (Streaming Parser for Event Logs using Longest Common Subsequence) algorithm,
implemented for batch or streaming. Since logs typically comprise repeating messages with
variable parts, this algorithm identifies the common templates (static parts), and for
each log line, distinguishes the template from the variable parts (parameters).