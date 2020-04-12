"""
Core functions for autonomous BitMEX bot.
"""

from time import sleep
from datetime import datetime

import backend.core as core
import backend.accounts as accounts

import bot.log as log
import bot.settings as settings


# Bot flags

kill_bot = False
new_entry = True
seconds = 3600


# Constants

PRICE_TYPE = "lastPrice"  # Which price data to use
                          # lastPrice, bidPrice, midPrice, askPrice

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
    account_name = accounts.get_all()[0]["name"]

    first_contract = settings.get_first_contract()
    second_contract = settings.get_second_contract()
    trade_difference = settings.get_trade_difference()
    close_difference = settings.get_close_difference()

    first_price = core.instrument_price(account_name, first_contract)[PRICE_TYPE]
    second_price = core.instrument_price(account_name, second_contract)[PRICE_TYPE]
    difference = abs(first_price - second_price)

    return {
        "time": datetime.now(),
        "contract1": first_contract,
        "contract2": second_contract,
        "price1": first_price,
        "price2": second_price,
        "difference": difference,
    }

def do_iteration():
    """
    Goes through bot routine: Compares prices and logs them.

    Called every configured interval of time by main bot function.
    """
    global new_entry

    results = compare()
    log.new_entry(results)
    new_entry = True

def main(on_iteration=lambda: None):
    """
    Main function of bot. Call to run bot.

    'on_iteration' will be called each time bot goes through its routine.
    """
    global kill_bot
    global seconds
    run = True

    while run:
        bot_sleeping = False
        do_iteration()
        on_iteration()
        bot_sleeping = True

        seconds = settings.get_interval()  # Check for kill flag while sleeping
        while seconds:
            sleep(1)
            if kill_bot:
                kill_bot = False
                run = False
                break
            seconds -= 1


# Outside control functions

def set_kill_flag_true():
    """
    Queues action for bot to kill its thread.
    """
    global kill_bot
    kill_bot = True

def has_new_entry():
    """
    Returns if new log entry was logged since last call to this function.
    """
    global new_entry
    foo = new_entry
    new_entry = False
    return foo

def get_seconds():
    """
    Returns how many seconds remain utill next bot iteration.
    """
    global seconds
    return seconds
