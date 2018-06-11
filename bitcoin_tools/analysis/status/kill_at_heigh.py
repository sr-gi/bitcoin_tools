from sys import argv
from getopt import getopt
from time import sleep
from os import kill
from signal import SIGTERM
import re

"""
The code in this file allows to kill a bitcoind process when it receives block at a given height by monitoring its
log file.

Usage:
    python kill_at_heigh.py -k block_heigh -p pid [-f file] [-o] [-e] "
    
where:
    block_height    is the block height at which the process will be killed,
    pid             is the pid of the bitcoind process,
    file            is the bitcoind log file (default path of this file is /home/USER/.bitcoin/debug.log),
    -o              is a flag to start reading at the origin of the log file, and
    -e              is a flag to start reading at the end of the log file.

It is useful to run bitcoind with:
    bitcoind -daemon -prune=550 && pidof bitcoind
"""

# Configuration parameters
SLEEP_INT = 0.5  # time I wait before checking again the log file for changes (seconds)

# Constants
START_AT_ORIGIN = 0
START_AT_END = -1


def kill_line(line, kill_at_height, pid):
    """
    Kills process with pid `pid` at when bitcoind is processing height `kill_at_height` (that is, if line
    contains a matching string).

    :param line: log file line to process
    :param kill_at_height: block height
    :param pid: pid of process to kill
    :return: False if not line does not match
    """
    if "UpdateTip: new best=" in line:
        try:
            height_str = re.search(' height=\d+ ', line)
            block_height = height_str.group()[8:-1]
            print "    Block height {} read".format(block_height)
            if block_height == kill_at_height:
                kill(pid, SIGTERM)
                print "Process with pid {} KILLED!!!".format(pid)
                exit()

        except AttributeError as err:
            return False

    return False


def follow(thefile, kill_at_height, pid, start_at=START_AT_ORIGIN):
    """
    Keeps reading a file indefinitely. Starts at the beginning of the file, at the end or where we left it.
    :param thefile: file that is read
    :param kill_at_height: block height
    :param pid: pid of process to kill
    :param start_at: where to start reading (START_AT_ORIGIN, START_AT_END, or offset).
    :return: 
    """

    # Define where we start
    if start_at == START_AT_END:
        thefile.seek(0, 2)  # offset 0 relative to file end (2)
    elif start_at != START_AT_ORIGIN:
        thefile.seek(start_at)  # offset start_at relative to the beginning of the file (default)

    # Keep reading forever!
    while True:
        line = thefile.readline()
        if line and not kill_line(line, kill_at_height, pid):
            continue
        if not line:
            print "Waiting {} for new data...".format(SLEEP_INT)
            sleep(SLEEP_INT)
            continue


if __name__ == '__main__':
    try:

        # Get params from call
        options, remainder = getopt(argv[1:], 'f:k:p:eo', ['file=', 'kill=', 'pid=', 'start-at-end', 'start-at-origin'])

        log_filename = "/home/cris/.bitcoin/debug.log"  # default log file
        start = START_AT_ORIGIN                         # default log file start
        kill_at_height, pid = None, None

        for opt, arg in options:
            if opt in ('-f', '--file'):
                log_filename = arg
            elif opt in ('-k', '--kill'):
                kill_at_height = arg
            elif opt in ('-p', '--pid'):
                pid = int(arg)
            elif opt in ('-e', '--start-at-end'):
                start = START_AT_END
            elif opt in ('-o', '--start-at-origin'):
                start = START_AT_ORIGIN

        if not kill_at_height or not pid:
            print "Usage: "
            print "    python kill_at_heigh.py -k block_heigh -p pid [-f file] [-o] [-e] "
            exit()

        print "Starting to monitor file {} at {}".format(log_filename, start)
        print "I'm going to kill process with pid {} at height {}".format(pid, kill_at_height)

        logfile = open(log_filename, "r")
        follow(logfile, kill_at_height, pid, start_at=start)

    except IOError as err:
        print "Bitcoind log file {} not found".format(log_filename)
