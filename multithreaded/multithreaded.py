"""
Contains classes with routines on their own threads.
"""

import threading

from time import sleep
from datetime import datetime

import backend.core as core
import backend.accounts as accounts

from backend.exceptions import BitmexBotException

import backend.log as log
import backend.botsettings as settings


#
# Classes
#


# Abstract classes

class Multithreaded:
    """
    Class from which all objects with their own threads should inherit.
    Abstract class.
    """

    REQUESTS_PER_MINUTE = 25
    DELAY_MULTIPLIER_ON_FAIL = 1

    def __init__(self, *args, **kwargs):
        self._kill_thread = False
        self.thread = None

        self.running = False
        self.seconds_remaining = 3600
        self.iterations_made = 0

        self.delay_multiplier = 1  # Will be set higher when an iteration fails

    def run(self):
        """
        Creates and starts objects thread.
        """
        self.thread = threading.Thread(target=self._main)
        self.thread.start()
        self.running = True

    def stop(self):
        """
        Kills objects thread.
        """
        self._kill_thread = True
        self.thread.join()
        self.running = False
        self.thread = None

    def is_running(self):
        """
        Returns if this objects thread is currently running.
        """
        return self.running

    def get_seconds(self):
        """
        Returns how many seconds currently remain untill next routine iteration.
        """
        return self.seconds_remaining

    def get_iterations_made(self):
        """
        Return how many successful iterations total has this object made.
        """
        return self.iterations_made

    def _do_iteration(self):
        """
        Called every configured interval of time by main bot function.
        Should be overridden in inheriting objects with actions to be done
        every iteration of this objects routine.
        Should return if this iteration was successful.
        Internal method.
        """
        return True

    def _get_delay(self):
        """
        Compute, how many seconds should this object wait before submitting
        more requests.
        Can be overridden in inheriting objects.
        Internal method.
        """
        delay = int(60 / self.REQUESTS_PER_MINUTE * self.delay_multiplier)
        return delay

    def _main(self):
        """
        Main function of object. Will be called on objects thread through run().
        Internal method.
        """
        run = True

        while run:
            if self._do_iteration():
                self.delay_multiplier = 1
                self.iterations_made += 1
            else:  # Spaces between iterations will get bigger and bigger as they fail
                self.delay_multiplier += self.DELAY_MULTIPLIER_ON_FAIL

            self.seconds_remaining = self._get_delay()
            while self.seconds_remaining > 0:  # Check kill flag every second
                sleep(1)
                if self._kill_thread:
                    self._kill_thread = False
                    run = False
                    break
                self.seconds_remaining -= 1


# Regular classes

class Bot(Multithreaded):
    """
    Class representing contract prices comparing bot.
    """

    REQUESTS_PER_MINUTE = 25

    PRICE_TYPE = "lastPrice"  # Which price data to use
                              # lastPrice, bidPrice, midPrice, askPrice

    def __init__(self, *args, **kwargs):
        Multithreaded.__init__(self, *args, **kwargs)
        self.new_entry = 1

    def has_new_entry(self):
        """
        Returns if new log entry was logged since last call to this function.
        """
        if self.new_entry:
            self.new_entry -= 1
            return True

    def _do_iteration(self):
        """
        Compare prices of confiured contracts and log results.
        Internal method.
        Overriding.
        """
        try:
            results = self._compare()
        except Exception as e:
            print(str(e))
            return False
        log.new_entry(results)
        self.new_entry = 2
        return True

    def _compare(self):
        """
        Compares prices of two configured contracts.
        Internal method.

        Returns dict of {
            time:       python timestamp of comparison,
            contract1:  symbol of first contract,
            contract2:  symbol of second contract,
            price1:     price of first contract,
            price2:     price of second contract,
            difference: difference between the prices,
        }.
        """
        account_name = settings.get_account()

        if not account_name:
            raise BitmexBotException("No account selected")

        first_contract = settings.get_first_contract()
        second_contract = settings.get_second_contract()
        trade_difference = settings.get_trade_difference()
        close_difference = settings.get_close_difference()

        first_price = core.instrument_price(account_name, first_contract)[self.PRICE_TYPE]
        second_price = core.instrument_price(account_name, second_contract)[self.PRICE_TYPE]
        difference = abs(first_price - second_price)

        return {
            "time": datetime.now(),
            "contract1": first_contract,
            "contract2": second_contract,
            "price1": first_price,
            "price2": second_price,
            "difference": difference,
        }


class Accounts(Multithreaded):
    """
    Class for monitoring wallet ballance and unrealised PnL for each account.
    """

    REQUESTS_PER_MINUTE = 25

    def __init__(self, *args, **kwargs):
        Multithreaded.__init__(self, *args, **kwargs)

        self.accounts = []

    def get_accounts(self):
        """
        Return last fetched statuses of accounts.
        Returns list of {
            "name": str,
            "stats": {
                "availableMargin": float,
                "unrealisedPnl": float
            }
        }
        """
        return self.accounts

    def _do_iteration(self):
        """
        Query backend for all accounts margin stats and save them in this object.
        Internal method.
        Overriding.
        """
        # Get all acount names
        names = [x["name"] for x in accounts.get_all()]

        # Get info
        try:
            accs = core.account_margin_stats(names)
        except Exception as e:
            print(str(e))
            return False

        accs.sort(key=lambda x: x["name"], reverse=False)  # Sort
        self.accounts = accs

        return True

    def _get_delay(self):
        """
        Compute, how many seconds should this object wait before submitting
        more requests with respect for how many accounts are requests sent.
        Internal method.
        Overriding.
        """
        delay = int(60 / self.REQUESTS_PER_MINUTE * len(accounts.get_all()))
        return delay


class Positions(Multithreaded):
    """
    Class for monitoring status of positions of each account.
    """

    REQUESTS_PER_MINUTE = 25

    def __init__(self, *args, **kwargs):
        Multithreaded.__init__(self, *args, **kwargs)

        self.positions = []

    def get_positions(self):
        """
        Return last fetched positions of accounts.
        Returns list of {
            "name": str,
            "positions": list of {
                "symbol": str,
                "size": int,
                "value": float,
                "notional": float,
                "entryPrice": float,
                "markPrice": float,
                "liqPrice": float,
                "margin": float,
                "leverage": str,
                "unrealisedPnl": float,
                "roePcnt": float,
                "realisedPnl": float,
                "riskLimit": int
            }
        }
        """
        return self.positions

    def _do_iteration(self):
        """
        Query backend for all accounts position stats and save them in this
        object.
        Internal method.
        Overriding.
        """
        # Get all acount names
        names = [x["name"] for x in accounts.get_all()]

        # Get info
        try:
            positions = core.position_info(names)
        except Exception as e:
            print(str(e))
            return False

        for account in positions:
            account["positions"].sort(key=lambda x: x["symbol"], reverse=False)
        self.positions = positions

        return True

    def _get_delay(self):
        """
        Compute, how many seconds should this object wait before submitting
        more requests with respect for how many accounts are requests sent.
        Internal method.
        Overriding.
        """
        delay = int(60 / self.REQUESTS_PER_MINUTE * len(accounts.get_all()))
        return delay
