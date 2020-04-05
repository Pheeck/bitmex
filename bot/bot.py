"""
Core functions for autonomous BitMEX bot.
"""

from time import sleep
from datetime import datetime

import backend.core as core

import bot.log as log
import bot.settings as settings


# Functions

def compare():
    """
    Compares prices of two configured contracts.

    Returns dict of {
        time:       python timestamp of comparison,
        contract1:  symbol of first contract,
        contract2:  symbol of second contract,
        price1:     price of first contract,
        price2:     price of second contract,
        difference: difference between the prices,
    }.
    """
    return {
        "time": datetime.now(),
        "contract1": "TEST",
        "contract2": "TEXT",
        "price1": 1,
        "price2": 2,
        "difference": 1,
    }  # TODO

def do_iteration():
    """
    Goes through bot routine: Compares prices and logs them.

    Called every configured interval of time by main bot function.
    """
    results = compare()
    log.new_entry(results)

def main(on_iteration=lambda: None):
    """
    Main function of bot. Call to run bot.

    'on_iteration' will be called each time bot goes through its routine.
    """
    while True:
        settings.load()
        do_iteration()
        on_iteration()
        sleep(settings.get_interval())
