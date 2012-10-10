# irv.py
## A simple python script for instant-runoff voting

Runs instant-runoff voting(http://en.wikipedia.org/wiki/Instant-runoff_voting)
and prints a full ranking of all eligible candidates to standard output.

### Usage
    python irv.py <input-file> <manual-mode>

If a second argument is NOT given, the script will run in semiautomatic mode,
where it runs all eliminations automatically (except eliminations for
unbreakable ties).

### Input format
The first line of the input should be a tab-separated list of candidate names,
and each following line should contain unique positive integers for votes and 0s
for abstentions (separated by any form of whitespace). See `example1.txt` and
`example2.txt`.

