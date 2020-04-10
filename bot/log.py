"""
Functions related to bot activity log.
"""

from datetime import datetime

from backend.exceptions import BitmexBotException


# Constants

SAVEFILE = "./botlog"
TIME_FORMAT = "%y/%m/%d %H:%M:%S"

#
# Functions
#

# Utility

def read_last_n_lines(n: int, file):
    """
    Returns last 'n' lines of file. Takes python file descriptor as argument.
    Naive implementation. Could be reworked later, if improved efficiency
    will be needed.
    """
    lines = file.readlines()[-n:]
    return lines


# Manipulating with log savefile

def reset(savefile: str = SAVEFILE):
    """
    Creates blank savefile. Warning: Replaces old savefile.
    """
    try:
        f = open(savefile, "w")
    except Exception as e:
        raise BitmexBotException(str(e))
    f.close()

    # Write a sample entry
    new_entry({
        "time": datetime.now(),
        "contract1": "SAM",
        "contract2": "PLE",
        "price1": 20,
        "price2": 40,
        "difference": 20,
    }, savefile)

def new_entry(results: dict, savefile: str = SAVEFILE):
    """
    Write new entry into log savefile with data from comparison results.
    Takes dict of {
        time:       python datetime timestamp of comparison,
        contract1:  symbol of first contract,
        contract2:  symbol of second contract,
        price1:     price of first contract,
        price2:     price of second contract,
        difference: difference between the prices,
    } as argument.
    """
    try:
        f = open(savefile, "a")
    except Exception as e:
        raise BitmexAccountsException(str(e))

    entry = results["time"].strftime(TIME_FORMAT) + "\t"
    entry += "{contract1}\t{price1}\t{contract2}\t{price2}\t{difference}\n".format(**results)

    f.write(entry)
    f.close()

def read_entries(n: int = 0, savefile: str = SAVEFILE):
    """
    Read 'n' last entries from savefile and return them. If 'n' set to 0, all
    lines will be read.
    Returns list of {
        time:       python datetime timestamp of comparison,
        contract1:  symbol of first contract,
        contract2:  symbol of second contract,
        price1:     price of first contract,
        price2:     price of second contract,
        difference: difference between the prices,
    } dicts.
    """
    f = None
    try:
        f = open(savefile, "r")
        # Note: Last line will be blank -> .pop(), n+1
        if n == 0:
            entries = read_lines()
            entries.pop()
        else:
            entries = read_last_n_lines(n + 1, f)
            entries.pop()
    except Exception as e:
        raise BitmexBotException("Internal Error: " + str(e) + " Does '" +
                                 savefile + "' really exist?")
    finally:
        if not f is None:
            f.close()

    for i, entry in enumerate(entries):
        entry = entry[:-1].split("\t")  # Get rid of newline and split
        try:
            entry = {
                "time": datetime.strptime(entry[0], TIME_FORMAT),
                "contract1": entry[1],
                "price1": float(entry[2]),
                "contract2": entry[3],
                "price2": float(entry[4]),
                "difference": float(entry[5]),
            }
        except Exception as e:
            raise BitmexBotException("Internal Error: " + str(e) + "Is '" +
                                     savefile + "' really a bot log savefile?")
        entries[i] = entry

    return entries
