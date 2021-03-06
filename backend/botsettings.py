"""
Saving and loading bot settings.
"""

from json import loads, dumps

from backend.exceptions import BitmexBotException


#
# Constants
#

SAVEFILE = "./botsettings"


#
# Settings dict
#

_settings = {  # Stores loaded settings, values here are defaults
    "contract1": "XBTUSD",
    "contract2": "XBTUSD",
    "tradeDiff": 1000,
    "closeDiff": 100,
    "account": "",
}


#
# Functions
#

# Getters and setters

def get_first_contract():
    """
    Returns configured symbol of first contract.
    """
    return _settings["contract1"]

def set_first_contract(symbol: str):
    """
    Set symbol of first contract.
    """
    _settings["contract1"] = symbol

def get_second_contract():
    """
    Returns configured symbol of second contract.
    """
    return _settings["contract2"]

def set_second_contract(symbol: str):
    """
    Set symbol of second contract.
    """
    _settings["contract2"] = symbol

def get_trade_difference():
    """
    Returns difference between contract prices that will execute trade.
    """
    return _settings["tradeDiff"]

def set_trade_difference(difference: int):
    """
    Set difference between contract prices that will execute trade.
    """
    _settings["tradeDiff"] = difference

def get_close_difference():
    """
    Returns difference between contract prices that will close the trade.
    """
    return _settings["closeDiff"]

def set_close_difference(difference: int):
    """
    Set difference between contract prices that will close the trade.
    """
    _settings["closeDiff"] = difference

def get_account():
    """
    Returns name of account which bot is supposed to use.
    """
    return _settings["account"]

def set_account(accountName: str):
    """
    Set account (by its name) which bot is supposed to use.
    """
    _settings["account"] = accountName


# Manipulating with savefile

def save(savefile: str = SAVEFILE):
    """
    Save settings to savefile. Warning: Replaces old savefile.
    """
    try:
        f = open(savefile, "w")
    except Exception as e:
        raise BitmexBotException(str(e))

    f.write(dumps(_settings))
    f.close()

def load(savefile: str = SAVEFILE):
    """
    Load settings from savefile.
    """
    try:
        f = open(savefile, "r")
    except Exception as e:
        raise BitmexBotException("Internal Error: " + str(e) + "Does '" +
                                 savefile + "' really exist?")

    json = f.read()
    f.close()

    try:
        dict = loads(json)
    except Exception as e:
        raise BitmexBotException("Internal Error: " + str(e) + "Is '" +
                                 savefile + "' really a bot settings savefile?")

    for key in _settings.keys():
        if not key in dict.keys():
            raise BitmexBotException("Internal Error: The '" + savefile +
                                     "' savefile is incomplete.")

    for key in _settings.keys():
        _settings[key] = dict[key]
