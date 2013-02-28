Sqlcanon is a tool that canonicalizes statements read from either log files, stdin or captured packets.

When applicable (especially when reading from log files) it also extracts additional data found and saved for reporting purposes.

Currently it has two parts: sqlcanonclient and sqlcanon server.  Sqlcanonclient is the one responsible for canonicalizing and extracting data. It has the option to pass data to sqlcanon server (in client-server mode) or just store them locally (stand-alone mode).

Current Features:

* Process MySQL slow query log
* Process MySQL general query log
* Process statements from captured packets
* Process statements from stdin
* Captured statements are stored as RRD.

See docs/sqlcanon.md for more information.
