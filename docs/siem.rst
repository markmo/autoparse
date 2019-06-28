Security Information and Event Management (SIEM)
================================================

Network security appliances like IDS devices, IPS devices, and firewalls generate an awful lot of logs.
A well-configured SIEM will alert security administrators to which events and trends they should pay
attention to. Otherwise they’ll be too lost in event log noise to be able to effectively handle possible
security threats to their network.

One of the key components that a functioning SIEM requires is good and sensible SIEM correlation rules.

What is a correlation rule?
---------------------------

The various appliances in your network should be constantly generating event logs that are fed into
your SIEM system. A SIEM correlation rule tells your SIEM system which sequences of events could be
indicative of anomalies which may suggest security weaknesses or cyber attack. When `x` and `y` or
`x` and `y` plus `z` happens, your administrators should be notified.

Here are some examples of SIEM correlation rules which illustrate this concept.

* Detect new DHCP servers in your network by watching for inside or outside connections which use
  UDP packets (`x`), have port 67 as the destination (`y`), and the destination IP address isn’t on the
  registered IP list (`z`).
* Warn administrators if five failed login attempts are tried with different usernames from the same IP
  to the same machine within fifteen minutes (`x`), if that event is followed by a successful login occurring
  from that same IP address to any machine inside the network (`y`).

The first example could indicate a cyber attacker establishing a DHCP server to acquire malicious access
to your network. Any authorized DHCP server would use one of your registered IP addresses!

The second example could indicate a cyber attacker brute-forcing an authentication vector and then
successfully acquiring authentication to your network. It could be a possible privilege escalation attack.

SIEM correlation rules can generate false positives just like any sort of event monitoring algorithm.

Example correlation rules:

* Connection established from some IP address and some TCP/IP port to another IP address and TCP/IP port.

* Some user changed their username on Tuesday and their password on Thursday

* Some client machine downloaded 500MB and uploaded 200MB of network traffic one day, then downloaded
  3.5GB and uploaded 750MB of network traffic the next day.

* Authentication and account events:

  * Large number of failed logon attempts
  * Alternation and usage of specific accounts (e.g. Directory Service Recovery Mode (DSRM) - Active
    Directory Account used for recovery purposes).
    
* Windows Security ID (SID) history

* Process execution:
  
  * Execution from unusual locations
  * Suspicious process relationships
  * Known executables with unknown hashes
  * Known evil hashes
  
* Windows events:
  
  * Service installations with rare names in monitored environment
  * New domain trusts
  
* Network:

  * Port scans
  * Host discovery (ping sweeps)

* Web applications:

  * 5xx errors
  * Specific exceptions


Event Log Normalization
-----------------------

Event log normalization is an effort to change event log formats from different vendors and network
components so they’re as universal as possible within your network.


Open Source Intrusion Detection Systems (IDS)
---------------------------------------------

1. `SNORT <https://www.snort.org/>`_ - network traffic / packet inspection - real-time traffic analysis
   and packet logging on Internet Protocol (IP) networks. Snort performs protocol analysis, content
   searching and matching.
2. `YARA <https://github.com/VirusTotal/yara>`_ - file analysis - identify and classify malware samples
3. `SIGMA <https://github.com/Neo23x0/sigma>`_ - signatures for log events. Sigma rules are written in YAML.


References:

1. `How SIEM Correlation Rules Work <https://www.alienvault.com/blogs/security-essentials/how-siem-correlation-rules-work>`_
2. `Open Source Intrusion Detection Tools: A Quick Overview <https://www.alienvault.com/blogs/security-essentials/open-source-intrusion-detection-tools-a-quick-overview>`_
3. `Sigma - Generic Signatures for Log Events - Thomas Patzke <https://www.youtube.com/watch?v=OheVuE9Ifhs>`_
