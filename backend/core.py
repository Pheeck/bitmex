"""
Core functions. Should be simple enought to be directly used by user.
"""

from sys import exc_info

from utility import significant_figures

import backend.api as api
import backend.accounts as accounts
from backend.exceptions import *


# Constants

HISTORY_COUNT = 20  # How many history orders to fetch
SIGNIFICANT_FIGURES = 5  # When rounding ints and floats


#
# Internal functions
#

# Utility

def _tick_round(quantity, tick):
    """
    Round quantity to fit BitMEX's quantity tick.

    quantity    number being rounded
    tick        rounding base

    Returns rounded number.
    """
    return tick * round(float(quantity) / tick)


# Api

def _for_each_account(accountNames, call, **params):
    """
    Call to API for each account.

    accountNames:   list of account names
    call:           api function
    params:         parameters for call

    Returns list of {"account": account dict, "response": response dict} for
    each successful call.
    """
    result = []
    coreExc = BitmexCoreMultiException()
    for name in accountNames:
        try:
            account = accounts.get(name)
        except Exception as e:
            coreExc.exceptions.append(e)
            coreExc.tracebacks.append(exc_info()[0])
            continue
        key = account["key"]
        secret = account["secret"]
        host = account["host"]
        try:
            response = call(host, key, secret, **params)
            dict = {
                "account": account,
                "response": response
            }
            result.append(dict)
        except Exception as e:
            coreExc.accounts.append(account)
            coreExc.exceptions.append(e)
            coreExc.tracebacks.append(exc_info()[0])
    if coreExc.exceptions:
        raise coreExc
    else:
        return result


def _for_each_relative(accountNames, call, percent, marginPerContract,
                       **params):
    """
    Call to API for each account with orderQty parameter relative to each accounts
    available margin (rounded to fit instrument tick).

    accountNames:       list of account names
    call:               api function
    percent:            order value = (percent / 100) * available margin
    marginPerContract:  how much margin is equal to one contract (in bitcoin)
    params:             parameters for call

    Returns list of {"account": account dict, "response": response dict} for
    each successful call.
    """
    result = []
    coreExc = BitmexCoreMultiException()
    # Get instrument tick size
    for name in accountNames:
        # Get account
        try:
            account = accounts.get(name)
        except Exception as e:
            coreExc.exceptions.append(e)
            coreExc.tracebacks.append(exc_info()[0])
            continue
        key = account["key"]
        secret = account["secret"]
        host = account["host"]
        # Get account available margin
        try:
            available = account_available_margin(name)
        except Exception as e:
            coreExc.accounts.append(account)
            coreExc.exceptions.append(e)
            coreExc.tracebacks.append(exc_info()[0])
            continue
        # Compute order quantity
        orderValue = percent / 100.0 * available  # * leverage
        orderQty = orderValue / marginPerContract
        orderQty = round(orderQty)
        params["orderQty"] = orderQty
        # Send api call
        try:
            response = call(host, key, secret, **params)
            dict = {
                "account": account,
                "response": response
            }
            result.append(dict)
        except Exception as e:
            coreExc.accounts.append(account)
            coreExc.exceptions.append(e)
            coreExc.tracebacks.append(exc_info()[0])
    if coreExc.exceptions:
        raise coreExc
    else:
        return result


def _for_one_account(accountName, call, **params):
    """
    Call to API for one account.

    accountName:    account name
    call:           api function
    params:         parameters for call

    Returns {"account": account dict, "response": response dict}.
    """
    # Get account
    account = None
    try:
        account = accounts.get(accountName)
    except Exception as e:
        raise BitmexCoreException(str(e))
    key = account["key"]
    secret = account["secret"]
    host = account["host"]

    # Call api
    try:
        response = call(host, key, secret, **params)
        return {
            "account": account,
            "response": response
        }
    except Exception as e:
        raise BitmexCoreException(account["name"] + ":\n" + str(e))
        raise coreExc


#
# Accounts
#

def account_available_margin(accountName):
    """
    Get available margin for account (in bitcoins).

    accountName:       which account

    Returns available margin float.
    """
    params = {
        "currency": "XBt"
    }
    response = _for_one_account(accountName, api.user_margin_get, **params)["response"]
    return response["availableMargin"] * 1e-8


def account_margin_stats(accountNames):
    """
    Get account margin statistics for each account (monetary values in bitcoins).

    accountNames:       list of names of accounts to use

    Returns list of {
        "account": str,
        "stats": {
            "availableMargin": float
            "unrealisedPnl": float
        }
    }.
    """
    result = []
    params = {
        "currency": "XBt"
    }

    data = _for_each_account(accountNames, api.user_margin_get, **params)
    for foo in data:  # for each account
        account = {
            "name": foo["account"]["name"],
            "stats": {
                "availableMargin": float(foo["response"]["availableMargin"]),
                "unrealisedPnl": significant_figures(foo["response"]["unrealisedPnl"] * 1e-8,
                                                     SIGNIFICANT_FIGURES),
            }
        }
        result.append(account)
    return result


#
# Instruments
#

def instrument_tick(accountName, symbol):
    """
    Get instruments tick size.

    accountName:    name of account (for authorization)
    symbol:         instruments symbol

    Returns tick size float.
    """
    params = {
        "symbol": symbol
    }
    response = _for_one_account(accountName, api.instrument_get, **params)["response"]
    return response[0]["tickSize"]


def instrument_is_inverse(accountName, symbol):
    """
    Find out if instrument prices are in CURRENCY/BITCOIN (inversed)

    accountName:    name of account (for authorization)
    symbol:         instruments symbol

    Returns true if inverse, false if not.
    """
    params = {
        "symbol": symbol
    }
    response = _for_one_account(accountName, api.instrument_get, **params)["response"]
    return response[0]["isInverse"]


def instrument_contract_value(accountName, symbol):
    """
    Get how much currency does one contract of specific instrument contain.

    accountName:    name of account (for authorization)
    symbol:         instruments symbol

    Returns contract value as float.
    """
    params = {
        "symbol": symbol
    }
    response = _for_one_account(accountName, api.instrument_get, **params)["response"]
    return abs(response[0]["multiplier"] * 1e-8)


def instrument_margin_per_contract(accountName, symbol, price,
                                   forceContractValue=None, forceInverse=None):
    """
    Get how much margin is in one contract for instrument.

    accountName:        name of account (for authorization)
    symbol:             instruments symbol
    price:              how much currency to buy one contract
    forceContractValue: if set to a value, overrides what server says about how
                        much currency is in one contract of this instrument
    forceInverse:       if set to true or false, overrides what server says about
                        this instruments inversion

    Returns margin per contract float.
    """
    if forceContractValue is None:
        # Get contract value
        try:
            contractValue = instrument_contract_value(accountName, symbol)
        except Exception as e:
            raise BitmexCoreException("Wasn't able to get " + symbol +
                                      "s contract value: " + str(e))
    else:
        contractValue = forceContractValue
    if forceInverse is None:
        # Get inverse
        try:
            inverse = instrument_is_inverse(accountName, symbol)
        except Exception as e:
            raise BitmexCoreException("Wasn't able to find out if " + symbol +
                                      " is inverse: " + str(e))
    else:
        inverse = forceInverse
    # Compute margin per contract
    if not inverse:
        marginPerContract = price * contractValue
    else:
        marginPerContract = (1 / price) * contractValue
    return marginPerContract


def open_instruments(accountName):
    """
    Get all open instruments.

    accountName:        name of account (for authorization)

    Returns list of symbol strings.
    """
    result = []
    response = _for_one_account(accountName, api.instrument_get,
                                filter={"state": "Open"})["response"]
    for instrument in response:
        result.append(instrument["symbol"])
    return result


def instrument_info(accountNames):
    """
    Get info about all instruments of each account.

    accountNames:       list of names of accounts to use

    Returns list of {
        "name": str,
        "instruments": list of {
            "symbol": str,
            "leverage": str,
            "riskLimit": str,
            "realisedPnl": str
        }
    }.
    """
    result = []
    # Get all currently open instruments
    data = _for_one_account(accountNames[0], api.instrument_get, filter={"state": "Open"})
    # Get positions of each account (there won't be all though)
    data2 = position_info_all(accountNames)
    for foo in data2:  # for each account
        account = {
            "name": foo["name"],
            "instruments": []
        }
        # Iterate through all open instruments. If we have a position with same
        # symbol, return that positions data. If we don't return just symbol.
        for instrument in data["response"]:
            # This list will contain one position if it was found. Otherwise,
            # it will be empty.
            position = [x for x in foo["positions"] if x["symbol"] == instrument["symbol"]]
            if position:  # It wasn't empty -> position found
                position = position[0]
                dict = {
                    "symbol": position["symbol"],
                    "leverage": str(position["leverage"]),
                    "riskLimit": str(position["riskLimit"]),
                    "realisedPnl": str(position["realisedPnl"])
                }
            else:  # It was empty -> return just symbol
                dict = {
                    "symbol": instrument["symbol"],
                    "leverage": "",
                    "riskLimit": "",
                    "realisedPnl": ""
                }
            account["instruments"].append(dict)
        result.append(account)
    return result


#
# Placing orders
#

# Limit

def order_limit(accountNames, symbol, quantity, limitPrice, sell=False, hidden=False,
                displayQty=0, timeInForce="GoodTillCancel", reduceOnly=False,
                stopLoss=False, stopPrice=None, trigger="Last"):
    """
    Send limit order for each account.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    quantity:       how many contracts in each order
    limitPrice:     buy/sell for this much
    sell:           true for sell order, false for buy order
    hidden:         true for displayQty to take effect
    displayQty:     how big should order appear in book
    timeInForce:    when should order expire
                        GoodTillCancel
                        ImmediateOrCancel
                        FillOrKill
    reduceOnly: true for reduce-only order which won't increase position
    stopLoss:           if set to true, also create mirroring close stop orders
    stopPrice:          trigger price of stop loss order
    trigger:            trigger type of stop loss order
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Generate execInst
    execInst = []
    if reduceOnly:
        execInst.append("ReduceOnly")

    params = {
        "symbol": symbol,
        "ordType": "Limit",
        "orderQty": quantity,
        "price": limitPrice,
        "execInst": ", ".join(execInst),
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    if hidden:
        params["displayQty"] = displayQty
    _for_each_account(accountNames, api.order_post, **params)
    # Stop loss
    execInst = ["ReduceOnly"]
    if stopLoss:
        params.pop("price")
        params["ordType"] = "Stop"
        params["stopPx"] = stopPrice
        params["side"] = "Buy" if params["side"] == "Sell" else "Sell"
        if trigger in ("Mark", "Last", "Index"):
            execInst.append(trigger + "Price")
        else:
            raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                      "Choose from Mark, Last and Index.")
        params["execInst"] = ", ".join(execInst)
        _for_each_account(accountNames, api.order_post, **params)


def order_limit_post_only(accountNames, symbol, quantity, limitPrice, sell=False,
                          reduceOnly=False, stopLoss=False, stopPrice=None,
                          trigger="Last"):
    """
    Send limit post-only order for each account.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    quantity:       how many contracts in each order
    limitPrice:     buy/sell for this much
    sell:           true for sell order, false for buy order
    reduceOnly:     true for reduce-only order which won't increase position
    stopLoss:           if set to true, also create mirroring close stop orders
    stopPrice:          trigger price of stop loss order
    trigger:            trigger type of stop loss order
    """
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if reduceOnly:
        execInst.append("ReduceOnly")

    params = {
        "symbol": symbol,
        "ordType": "Limit",
        "orderQty": quantity,
        "price": limitPrice,
        "execInst": ", ".join(execInst),
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)
    # Stop loss
    execInst = ["ReduceOnly"]
    if stopLoss:
        params.pop("price")
        params["ordType"] = "Stop"
        params["stopPx"] = stopPrice
        params["side"] = "Buy" if params["side"] == "Sell" else "Sell"
        if trigger in ("Mark", "Last", "Index"):
            execInst.append(trigger + "Price")
        else:
            raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                      "Choose from Mark, Last and Index.")
        params["execInst"] = ", ".join(execInst)
        _for_each_account(accountNames, api.order_post, **params)


def order_stop_limit(accountNames, symbol, quantity, limitPrice, stopPrice,
                     sell=False, trigger="Last", closeOnTrigger=False,
                     hidden=False, displayQty=0, timeInForce="GoodTillCancel"):
    """
    Send stop limit order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    limitPrice:         buy/sell for this much
    stopPrice:          where should stop order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    hidden:             true for displayQty to take effect
    displayQty:         how big should order appear in book
    timeInForce:        when should order expire
                            GoodTillCancel
                            ImmediateOrCancel
                            FillOrKill
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        "orderQty": quantity,
        "price": limitPrice,
        "stopPx": stopPrice,
        "execInst": execInst,
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    if hidden:
        params["displayQty"] = displayQty
    _for_each_account(accountNames, api.order_post, **params)


def order_stop_limit_post_only(accountNames, symbol, quantity, limitPrice, stopPrice,
                               sell=False, trigger="Last", closeOnTrigger=False):
    """
    Send stop limit post-only order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    limitPrice:         buy/sell for this much
    stopPrice:          where should stop order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    """
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        "orderQty": quantity,
        "price": limitPrice,
        "stopPx": stopPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)


def order_take_profit_limit(accountNames, symbol, quantity, limitPrice, triggerPrice,
                            sell=False, trigger="Last", closeOnTrigger=False,
                            hidden=False, displayQty=0, timeInForce="GoodTillCancel"):
    """
    Send take profit limit order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    limitPrice:         buy/sell for this much
    triggerPrice:       where should stop order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:         true for close order
    hidden:             true for displayQty to take effect
    displayQty:         how big should order appear in book
    timeInForce:        when should order expire
                            GoodTillCancel
                            ImmediateOrCancel
                            FillOrKill
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        "orderQty": quantity,
        "price": limitPrice,
        "stopPx": triggerPrice,
        "execInst": execInst,
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    if hidden:
        params["displayQty"] = displayQty
    _for_each_account(accountNames, api.order_post, **params)


def order_take_profit_limit_post_only(accountNames, symbol, quantity, limitPrice,
                                      triggerPrice, sell=False, trigger="Last",
                                      closeOnTrigger=False):
    """
    Send take profit limit post-only order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    limitPrice:         buy/sell for this much
    triggerPrice:       where should stop order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    """
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "LimitIfTouched",
        "orderQty": quantity,
        "price": limitPrice,
        "stopPx": triggerPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)


# Limit relative

def order_limit_relative(accountNames, symbol, percent, limitPrice,
                         sell=False, hidden=False, displayQty=0,
                         timeInForce="GoodTillCancel", reduceOnly=False,
                         forceContractValue=None, forceInverse=None,
                         stopLoss=False, stopPrice=None, trigger="Last"):
    """
    Send limit order for each account with order quantity relative to account
    available margin.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    percent:            order value = (percent / 100) * available margin
    limitPrice:         buy/sell for this much
    sell:               true for sell order, false for buy order
    hidden:             true for displayQty to take effect
    displayQty:         how big should order appear in book
    timeInForce:        when should order expire
                            GoodTillCancel
                            ImmediateOrCancel
                            FillOrKill
    reduceOnly:         true for reduce-only order which won't increase position
    forceContractValue: if set to a value, overrides what server says about how
                        much currency is in one contract of this instrument
    forceInverse:       if set to true or false, overrides what the server says
                        about this instruments inversion
    stopLoss:           if set to true, also create mirroring close stop orders
    stopPrice:          trigger price of stop loss order
    trigger:            trigger type of stop loss order
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    if reduceOnly:
        execInst.append("ReduceOnly")

    params = {
        "symbol": symbol,
        "ordType": "Limit",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "execInst": ", ".join(execInst),
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    # Send orders
    responses = _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                                   **params)
    # Stop loss
    execInst = ["ReduceOnly"]
    if stopLoss:
        params.pop("price")
        params["ordType"] = "Stop"
        params["stopPx"] = stopPrice
        params["side"] = "Buy" if params["side"] == "Sell" else "Sell"
        if trigger in ("Mark", "Last", "Index"):
            execInst.append(trigger + "Price")
        else:
            raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                      "Choose from Mark, Last and Index.")
        params["execInst"] = ", ".join(execInst)
        for response in responses:
            account = response["account"]["name"]
            orderQty = response["response"]["orderQty"]
            params["orderQty"] = orderQty
            _for_one_account(account, api.order_post, **params)


def order_limit_relative_post_only(accountNames, symbol, percent, limitPrice,
                                   sell=False, reduceOnly=False,
                                   forceContractValue=None, forceInverse=None,
                                   stopLoss=False, stopPrice=None, trigger="Last"):
    """
    Send limit post-only order for each account with order quantity relative to
    account available margin.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    percent:            order value = (percent / 100) * available margin
    limitPrice:         buy/sell for this much
    sell:               true for sell order, false for buy order
    reduceOnly:         true for reduce-only order which won't increase position
    forceContractValue: if set to a value, overrides what server says about how
                        much currency is in one contract of this instrument
    forceInverse:       if set to true or false, overrides what the server says
                        about this instruments inversion
    stopLoss:           if set to true, also create mirroring close stop orders
    stopPrice:          trigger price of stop loss order
    trigger:            trigger type of stop loss order
    """
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if reduceOnly:
        execInst.append("ReduceOnly")

    params = {
        "symbol": symbol,
        "ordType": "Limit",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "execInst": ", ".join(execInst),
        "side": "Sell" if sell else "Buy"
    }
    responses = _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                                   **params)
    # Stop loss
    execInst = ["ReduceOnly"]
    if stopLoss:
        params.pop("price")
        params["ordType"] = "Stop"
        params["stopPx"] = stopPrice
        params["side"] = "Buy" if params["side"] == "Sell" else "Sell"
        if trigger in ("Mark", "Last", "Index"):
            execInst.append(trigger + "Price")
            params["execInst"] = ", ".join(execInst)
        else:
            raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                      "Choose from Mark, Last and Index.")
        for response in responses:
            account = response["account"]["name"]
            orderQty = response["response"]["orderQty"]
            params["orderQty"] = orderQty
            _for_one_account(account, api.order_post, **params)


def order_stop_limit_relative(accountNames, symbol, percent, limitPrice, stopPrice,
                              sell=False, trigger="Last", closeOnTrigger=False,
                              hidden=False, displayQty=0, timeInForce="GoodTillCancel",
                              forceContractValue=None, forceInverse=None):
    """
    Send stop limit order for each account with order quantity relative to
    account available margin.

    accountNames:           list of names of accounts to use
    symbol:                 symbol of position
    percent:                order value = (percent / 100) * available margin
    limitPrice:             buy/sell for this much
    stopPrice:              where should stop order trigger
    sell:                   true for sell order, false for buy order
    trigger:                type of trigger
                                Mark
                                Last
                                Index
    closeOnTrigger:             true for close order
    hidden:                 true for displayQty to take effect
    displayQty:             how big should order appear in book
    timeInForce:            when should order expire
                                GoodTillCancel
                                ImmediateOrCancel
                                FillOrKill
    forceContractValue:     if set to a value, overrides what server says about how
                            much currency is in one contract of this instrument
    forceInverse:           if set to true or false, overrides what the server says
                            about this instruments inversion
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "stopPx": stopPrice,
        "execInst": execInst,
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    if hidden:
        params["displayQty"] = displayQty
    _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                       **params)


def order_stop_limit_relative_post_only(accountNames, symbol, percent, limitPrice,
                                        stopPrice, sell=False, trigger="Last",
                                        closeOnTrigger=False, forceContractValue=None,
                                        forceInverse=None):
    """
    Send stop limit post-only order for each account with order quantity relative to
    account available margin.

    accountNames:           list of names of accounts to use
    symbol:                 symbol of position
    percent:                order value = (percent / 100) * available margin
    limitPrice:             buy/sell for this much
    stopPrice:              where should stop order trigger
    forceContractValue:     if set to a value, overrides what server says about how
                            much currency is in one contract of this instrument
    forceInverse:           if set to true or false, overrides what the server says
                            about this instruments inversion
    sell:                   true for sell order, false for buy order
    trigger:                type of trigger
                                Mark
                                Last
                                Index
    closeOnTrigger:         true for close order
    """
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "stopPx": stopPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                       **params)


def order_take_profit_limit_relative(accountNames, symbol, percent, limitPrice,
                                     triggerPrice, forceContractValue=None, forceInverse=None,
                                     sell=False, trigger="Last", closeOnTrigger=False,
                                     hidden=False, displayQty=0, timeInForce="GoodTillCancel"):
    """
    Send take profit limit order for each account with order quantity relative to
    account available margin.

    accountNames:           list of names of accounts to use
    symbol:                 symbol of position
    percent:                order value = (percent / 100) * available margin
    limitPrice:             buy/sell for this much
    triggerPrice:           where should stop order trigger
    forceContractValue:     if set to a value, overrides what server says about how
                            much currency is in one contract of this instrument
    forceInverse:           if set to true or false, overrides what the server says
                            about this instruments inversion
    sell:                   true for sell order, false for buy order
    trigger:                type of trigger
                                Mark
                                Last
                                Index
    closeOnTrigger:             true for close order
    hidden:                 true for displayQty to take effect
    displayQty:             how big should order appear in book
    timeInForce:            when should order expire
                                GoodTillCancel
                                ImmediateOrCancel
                                FillOrKill
    """
    if timeInForce not in ("GoodTillCancel", "ImmediateOrCancel", "FillOrKill"):
        raise BitmexCoreException(str(trigger) + " isn't a valid time in force. "
                                  + "Choose from GoodTillCancel, ImmediateOrCancel "
                                  + "and FillOrKill.")
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "StopLimit",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "stopPx": triggerPrice,
        "execInst": execInst,
        "timeInForce": timeInForce,
        "side": "Sell" if sell else "Buy"
    }
    if hidden:
        params["displayQty"] = displayQty
    _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                       **params)


def order_take_profit_limit_relative_post_only(accountNames, symbol, percent, limitPrice,
                                               triggerPrice, forceContractValue=None,
                                               forceInverse=None, sell=False, trigger="Last",
                                               closeOnTrigger=False):
    """
    Send take profit limit post-only order for each account with order quantity relative to
    account available margin.

    accountNames:           list of names of accounts to use
    symbol:                 symbol of position
    percent:                order value = (percent / 100) * available margin
    limitPrice:             buy/sell for this much
    forceContractValue:     if set to a value, overrides what server says about how
                            much currency is in one contract of this instrument
    triggerPrice:           where should stop order trigger
    forceInverse:           if set to true or false, overrides what the server says
                            about this instruments inversion
    sell:                   true for sell order, false for buy order
    trigger:                type of trigger
                                Mark
                                Last
                                Index
    closeOnTrigger:         true for close order
    """
    # Get margin per contract
    try:
        marginPerContract = instrument_margin_per_contract(accountNames[0], symbol,
                                                           limitPrice, forceContractValue,
                                                           forceInverse)
    except Exception as e:
        raise BitmexCoreException("Wasn't able to find out " + symbol +
                                  "s margin per contract: " + str(e))
    # Generate execInst
    execInst = []
    execInst.append("ParticipateDoNotInitiate")
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "LimitIfTouched",
        # "orderQty": quantity, (will be added in _for_each_relative)
        "price": limitPrice,
        "stopPx": triggerPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_relative(accountNames, api.order_post, percent, marginPerContract,
                       **params)


# Market

def order_market(accountNames, symbol, quantity, sell=False, stopLoss=False,
                 stopPrice=None, trigger="Last"):
    """
    Send market order for each account.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    quantity:       how many contracts in each order
    sell:           true for sell order, false for buy order
    reduceOnly:     true for reduce-only order which won't increase position
    stopLoss:       if set to true, also create mirroring close stop orders
    stopPrice:      trigger price of stop loss order
    trigger:        trigger type of stop loss order
    """
    params = {
        "symbol": symbol,
        "ordType": "Market",
        "orderQty": quantity,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)
    # Stop loss
    execInst = ["ReduceOnly"]
    if stopLoss:
        params.pop("price")
        params["ordType"] = "Stop"
        params["stopPx"] = stopPrice
        params["side"] = "Buy" if params["side"] == "Sell" else "Sell"
        if trigger in ("Mark", "Last", "Index"):
            execInst.append(trigger + "Price")
            params["execInst"] = ", ".join(execInst)
        else:
            raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                      "Choose from Mark, Last and Index.")
        _for_each_account(accountNames, api.order_post, **params)


def order_stop_market(accountNames, symbol, quantity, stopPrice, sell=False,
                      trigger="Last", closeOnTrigger=False):
    """
    Send stop market order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    stopPrice:          where should stop order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    """
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "Stop",
        "orderQty": quantity,
        "stopPx": stopPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)


def order_take_profit_market(accountNames, symbol, quantity, triggerPrice, sell=False,
                             trigger="Last", closeOnTrigger=False):
    """
    Send take profit market order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    triggerPrice:       where should take profit order trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    """
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "MarketIfTouched",
        "orderQty": quantity,
        "stopPx": triggerPrice,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)


def order_trailing_stop(accountNames, symbol, quantity, trailValue, sell=False,
                        trigger="Last", closeOnTrigger=False):
    """
    DO NOT USE, DOESN'T WORK
    Send trailing stop order for each account.

    accountNames:       list of names of accounts to use
    symbol:             symbol of position
    quantity:           how many contracts in each order
    trailValue:         offset of current value (therefore can be negative) where
                        trailing stop order should trigger
    sell:               true for sell order, false for buy order
    trigger:            type of trigger
                            Mark
                            Last
                            Index
    closeOnTrigger:     true for close order
    """
    # Generate execInst
    execInst = []
    if closeOnTrigger:
        execInst.append("Close")
    if trigger in ("Mark", "Last", "Index"):
        execInst.append(trigger + "Price")
    else:
        raise BitmexCoreException(str(trigger) + " isn't a valid trigger. " +
                                  "Choose from Mark, Last and Index.")
    execInst = ", ".join(execInst)

    params = {
        "symbol": symbol,
        "ordType": "Stop",
        "orderQty": quantity,
        "pegOffsetValue": trailValue,
        "execInst": execInst,
        "side": "Sell" if sell else "Buy"
    }
    _for_each_account(accountNames, api.order_post, **params)


#
# Positions
#

# Getting position info

def position_info(accountNames):
    """
    Get info about open positions of each account.

    accountNames:       list of names of accounts to use

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
    }.
    """
    result = []
    data = _for_each_account(accountNames, api.position_get, filter={"isOpen": True})
    for foo in data:
        account = {
            "name": foo["account"]["name"],
            "positions": []
        }
        for position in foo["response"]:
            if position["crossMargin"]:
                leverage = "cross"
            else:
                leverage = str(position["leverage"])
            dict = {
                "symbol": position["symbol"],
                "size": position["currentQty"],
                "value": abs(position["homeNotional"]),
                "notional": abs(position["foreignNotional"]),
                "entryPrice": position["avgEntryPrice"],
                "markPrice": position["markPrice"],
                "liqPrice": position["liquidationPrice"],
                "margin": significant_figures(position["posMargin"] * 1e-8,
                                              SIGNIFICANT_FIGURES),
                "leverage": leverage,
                "unrealisedPnl": significant_figures(position["unrealisedPnl"] * 1e-8,
                                                     SIGNIFICANT_FIGURES),
                "roePcnt": significant_figures(position["unrealisedRoePcnt"] * 100,
                                               SIGNIFICANT_FIGURES),
                "realisedPnl": significant_figures(position["realisedPnl"] * 1e-8,
                                                   SIGNIFICANT_FIGURES),
                "riskLimit": position["riskLimit"] * 1e-8
            }
            account["positions"].append(dict)
        result.append(account)
    return result


def position_info_all(accountNames):
    """
    Get info about open and closed positions.

    accountNames:       list of names of accounts to use

    Returns list of {
        "name": str,
        "positions": list of {
            "symbol": str,
            "realisedPnl": float,
            "leverage": str,
            "riskLimit": int
        }
    }.
    """
    result = []
    data = _for_each_account(accountNames, api.position_get)
    for foo in data:
        account = {
            "name": foo["account"]["name"],
            "positions": []
        }
        for position in foo["response"]:
            if position["crossMargin"]:
                leverage = "cross"
            else:
                leverage = str(position["leverage"])
            if position["riskLimit"] is None:
                riskLimit = ""
            else:
                riskLimit = position["riskLimit"] * 1e-8
            dict = {
                "symbol": position["symbol"],
                "realisedPnl": significant_figures(position["realisedPnl"],
                                                   SIGNIFICANT_FIGURES),
                "leverage": leverage,
                "riskLimit": riskLimit
            }
            account["positions"].append(dict)
        result.append(account)
    return result


# Amending positions

def position_leverage(accountNames, symbol, leverage):
    """
    Change leverage of position for each account.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    leverage:       new leverage
    """
    params = {
        "symbol": symbol,
        "leverage": leverage
    }
    _for_each_account(accountNames, api.position_leverage_post, **params)


def position_risk_limit(accountNames, symbol, riskLimit):
    """
    Change leverage of position for each account.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    riskLimit:      new risk limit
    """
    params = {
        "symbol": symbol,
        "riskLimit": riskLimit * 1e8  # Risk limit is in satoshis
    }
    _for_each_account(accountNames, api.position_risk_limit_post, **params)


def position_transfer_margin(accountNames, symbol, amount):
    """
    Change leverage of position for each account. Warning: Doesn't work.

    accountNames:   list of names of accounts to use
    symbol:         symbol of position
    ammount:        how much margin to transfer (can be negative)
    """
    params = {
        "symbol": symbol,
        "amount": amount * 1e8  # Margin is in satoshis
    }
    _for_each_account(accountNames, api.position_transfer_margin_post, **params)


#
# Orders
#

# Getting order info

def active_order_info(accountNames):
    """
    Get info about active non-stop non-take-profit orders of each account.

    accountNames:       list of names of accounts to use

    Returns list of {
        "name": str,
        "orders": list of {
            "orderID": str,
            "symbol": str,
            "qty": int,
            "orderPrice": float,
            "displayQty": int,
            "filled": int,
            "remaining": int,
            "orderValue": float,
            "fillPrice": float,
            "type": str,
            "status": str,
            "execInst": str,
            "time": datetime
        }
    }.
    """
    result = []
    data = _for_each_account(accountNames, api.order_get, filter={"open": True})
    for foo in data:
        account = {
            "name": foo["account"]["name"],
            "orders": []
        }
        for order in foo["response"]:
            if not order["ordType"] in ("Market", "Limit"):  # Skip stop and take profit orders
                continue
            if order["ordType"] == "Limit":
                orderValue = instrument_margin_per_contract(accountNames[0], order["symbol"],
                                                            order["price"])
                orderValue *= order["orderQty"]
            else:
                orderValue = None
            dict = {
                "orderID": order["orderID"],
                "symbol": order["symbol"],
                "qty": order["orderQty"] * (-1 if order["side"] == "Sell" else 1),
                "orderPrice": order["price"],
                "displayQty": order["displayQty"],
                "filled": order["orderQty"] - order["leavesQty"],
                "orderValue": orderValue,
                "remaining": order["leavesQty"],
                "fillPrice": order["avgPx"],
                "type": order["ordType"],
                "status": order["ordStatus"],
                "execInst": order["execInst"],
                "time": order["transactTime"]
            }
            account["orders"].append(dict)
        result.append(account)
    return result


def stop_order_info(accountNames):
    """
    Get info about active stop and take profit orders of each account.

    accountNames:       list of names of accounts to use

    Returns list of {
        "name": str,
        "orders": list of {
            "orderID": str,
            "symbol": str,
            "qty": int,
            "orderPrice": float,
            "filled": int,
            "stopPrice": float,
            "fillPrice": float,
            "type": str,
            "status": str,
            "execInst": str,
            "time": datetime
        }
    }.
    """
    result = []
    data = _for_each_account(accountNames, api.order_get, filter={"open": True})
    for foo in data:
        account = {
            "name": foo["account"]["name"],
            "orders": []
        }
        for order in foo["response"]:
            if order["ordType"] in ("Market", "Limit"):  # Only stop and take profit orders
                continue
            dict = {
                "orderID": order["orderID"],
                "symbol": order["symbol"],
                "qty": order["orderQty"] * -1 if order["side"] == "Sell" else 1,
                "orderPrice": order["price"],
                "filled": order["orderQty"] - order["leavesQty"],
                "stopPrice": order["stopPx"],
                "fillPrice": order["avgPx"],
                "type": order["ordType"],
                "status": order["ordStatus"],
                "execInst": order["execInst"],
                "time": order["transactTime"]
            }
            account["orders"].append(dict)
        result.append(account)
    return result


def history_order_info(accountNames):
    """
    Get info about non-active orders of each account.

    accountNames:       list of names of accounts to use

    Returns list of {
        "name": str,
        "orders": list of {
            "orderID": str,
            "symbol": str,
            "qty": int,
            "orderPrice": float,
            "displayQty": int,
            "filled": int,
            "stopPrice": float,
            "fillPrice": float,
            "type": str,
            "status": str,
            "execInst": str,
            "time": datetime
        }
    }.
    """
    result = []
    data = _for_each_account(accountNames, api.order_get, reverse=True, count=HISTORY_COUNT)
    for foo in data:
        account = {
            "name": foo["account"]["name"],
            "orders": []
        }
        for order in foo["response"]:
            dict = {
                "orderID": order["orderID"],
                "symbol": order["symbol"],
                "qty": order["orderQty"] * -1 if order["side"] == "Sell" else 1,
                "orderPrice": order["price"],
                "displayQty": order["displayQty"],
                "filled": order["orderQty"] - order["leavesQty"],
                "stopPrice": order["stopPx"],
                "fillPrice": order["avgPx"],
                "type": order["ordType"],
                "status": order["ordStatus"],
                "execInst": order["execInst"],
                "time": order["transactTime"]
            }
            account["orders"].append(dict)
        result.append(account)
    return result


# Amending orders

def order_qty(accountName, orderID, qty):
    """
    Amend contract quantity of order.

    accountName:    name of account of order
    orderID:        id of order
    qty:            new number of contracts
    """
    params = {
        "orderID": orderID,
        "orderQty": qty
    }
    _for_one_account(accountName, api.order_put, **params)


def order_price(accountName, orderID, orderPrice):
    """
    Amend limit price of order.

    accountName:    name of account of order
    orderID:        id of order
    orderPrice:     new limit price
    """
    params = {
        "orderID": orderID,
        "price": orderPrice
    }
    _for_one_account(accountName, api.order_put, **params)


def order_stop_price(accountName, orderID, stopPrice):
    """
    Amend stop price of order.

    accountName:    name of account of order
    orderID:        id of order
    stopPrice:      new stop price
    """
    params = {
        "orderID": orderID,
        "stopPx": stopPrice
    }
    _for_one_account(accountName, api.order_put, **params)


def order_cancel(accountName, orderID):
    """
    Cancel order.

    accountName:    name of account of order
    orderID:        id of order
    """
    params = {
        "orderID": orderID
    }
    _for_one_account(accountName, api.order_delete, **params)
