"""
Frames for landing page window.
"""

import tkinter


#
# Classes
#

class Menu(tkinter.Frame):
    """
    Frame for opening additional windows.
    """

    pass


class Overview(tkinter.Frame):
    """
    Frame displaying current global BitMEX statistics.
    """

    pass


class Accounts(tkinter.Frame):
    """
    Frame displaying wallet ballance and unrealised PnL for each account.
    """

    pass


class Positions(tkinter.Frame):
    """
    Frame for monitoring status of open positions for each account.
    """

    REQUESTS_PER_MINUTE = 25  # Window will try to respect this number
    REQUESTS_FASTER = 55
    MIN_DOTS = 1
    MAX_DOTS = 5
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    VAR = (
        "size",
        "notional",  # TODO Tento frame, zacni tim, ze orezes zobrazovane
        "entryPrice",
        "markPrice",
        "liqPrice",
        "margin",
        "leverage",
        "unrealisedPnl",
        "roePcnt",
        "realisedPnl",
        "riskLimit"
    )
    TEXT = (
        "Size",
        "Notional",
        "Entry Price",
        "Mark Price",
        "Liq. Price",
        "Margin",
        "Leverage",
        "Unrealised PNL",
        "ROE %",
        "Realised PNL",
        "Risk Limit"
    )
    WIDTH = (
        40,
        100,
        100,
        100,
        100,
        100,
        100,
        80,
        120,
        60,
        110,
        90
    )


class Order(tkinter.Frame):
    """
    Frame for creating new orders.
    """

    pass
