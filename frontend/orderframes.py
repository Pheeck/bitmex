"""
Frames for order windows.
"""

import tkinter
import tkinter.messagebox
import tkinter.ttk

import backend.accounts as accounts
import backend.core as core


#
# Constants
#

SPINBOX_LIMIT = 1000000000


#
# Classes
#

class Main(tkinter.Frame):
    """
    Frame present in every order window. Requires parent to have send() method.
    """

    COMBO_PARAMS = {
        "width": 9
    }
    SPINBOX_PARAMS = {
        "width": 9
    }
    BUTTON_PARAMS = {
        "width": 15
    }

    def __init__(self, parent, window, *args, **kvargs):
        tkinter.Frame.__init__(self, parent, *args, **kvargs)

        # Backend
        try:
            openInstruments = core.open_instruments(accounts.get_all()[0]["name"])
            openInstruments.sort()
        except Exception as e:
            print(e)
            openInstruments = []

        # Frontend
        self.symbolVar = tkinter.StringVar(self)

        symbolLabel = tkinter.Label(self, text="Symbol:")
        symbolCombo = tkinter.ttk.Combobox(self, textvariable=self.symbolVar,
                                           **self.COMBO_PARAMS)
        symbolCombo["values"] = openInstruments
        self.qtyLabel = tkinter.Label(self, text="Quantity:")
        self.qtySpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT,
                                       **self.SPINBOX_PARAMS)
        buyButton = tkinter.Button(self, text="Buy/Long",
                                   command=lambda: window._send(sell=False),
                                   **self.BUTTON_PARAMS)
        sellButton = tkinter.Button(self, text="Sell/Short",
                                    command=lambda: window._send(sell=True),
                                    **self.BUTTON_PARAMS)

        symbolLabel.grid(column=0, row=0)
        symbolCombo.grid(column=1, row=0)
        self.qtyLabel.grid(column=0, row=1)
        self.qtySpin.grid(column=1, row=1)
        buyButton.grid(column=0, row=2)
        sellButton.grid(column=1, row=2)

    def get_symbol(self):
        """
        Returns current text in symbol entry.
        """
        return str(self.symbolVar.get())

    def get_qty(self):
        """
        Returns current number in quantity spinbox.
        """
        return float(self.qtySpin.get())


class Accounts(tkinter.Frame):
    """
    Frame for choosing to which accounts should the order be sent.
    """

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        label = tkinter.Label(self, text="Select Accounts:")
        label.pack(anchor=tkinter.W)

        self.names = []
        self.vars = []

        for account in accounts.get_all():
            name = account["name"]
            var = tkinter.IntVar(self)

            check = tkinter.Checkbutton(self, text=name, var=var)
            check.pack(anchor=tkinter.W)

            self.names.append(name)
            self.vars.append(var)

    def get_names(self):
        """
        Returns currently selected account names.
        """
        result = []
        for name, var in zip(self.names, self.vars):
            if var.get():
                result.append(str(name))
        return result


class Limit(tkinter.Frame):
    """
    Frame present in every limit order window.
    """

    TIF = [
        "GoodTillCancel",
        "ImmediateOrCancel",
        "FillOrKill"
    ]
    SPINBOX_PARAMS = {
        "width": 9
    }
    OPTION_MENU_PARAMS = {
        "width": 20
    }

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.poVar = tkinter.IntVar(self)
        self.hiddVar = tkinter.IntVar(self)
        self.tifVar = tkinter.StringVar(self)
        self.roVar = tkinter.IntVar(self)

        self.tifVar.set(self.TIF[0])

        pxLabel = tkinter.Label(self, text="Limit Price:")
        self.pxSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT,
                                      **self.SPINBOX_PARAMS)
        poCheck = tkinter.Checkbutton(self, text="Post-Only", var=self.poVar)
        hiddCheck = tkinter.Checkbutton(self, text="Hidden", var=self.hiddVar)
        dispLabel = tkinter.Label(self, text="Display Quantity:")
        self.dispSpin = tkinter.Spinbox(self, from_=0, to=SPINBOX_LIMIT,
                                        **self.SPINBOX_PARAMS)
        tifOption = tkinter.OptionMenu(self, self.tifVar, *self.TIF)
        tifOption.configure(**self.OPTION_MENU_PARAMS)
        self.roCheck = tkinter.Checkbutton(self, text="Reduce-Only", var=self.roVar)

        pxLabel.grid(column=0, row=0)
        self.pxSpin.grid(column=1, row=0)
        poCheck.grid(column=0, row=1)
        hiddCheck.grid(column=1, row=1)
        dispLabel.grid(column=0, row=2)
        self.dispSpin.grid(column=1, row=2)
        tifOption.grid(column=0, row=3)
        self.roCheck.grid(column=1, row=3)

    def get_limit_price(self):
        """
        Returns current number in limit price spinbox.
        """
        return float(self.pxSpin.get())

    def get_post_only(self):
        """
        Returns if post only is checked.
        """
        return bool(self.poVar.get())

    def get_hidden(self):
        """
        Returns if hidden is checked.
        """
        return bool(self.hiddVar.get())

    def get_display_qty(self):
        """
        Returns current number in display quantity spinbox.
        """
        return float(self.dispSpin.get())

    def get_time_in_force(self):
        """
        Returns currently selected string in time in force option menu.
        """
        return str(self.tifVar.get())

    def get_reduce_only(self):
        """
        Returns if reduce only is checked.
        """
        return bool(self.roVar.get())


class Trigger(tkinter.Frame):
    """
    Frame present in every trigger order window.
    """

    TRIGGER_TYPES = [
        "Mark",
        "Last",
        "Index"
    ]
    OPTION_PARAMS = {
        "width": 9
    }

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.typeVar = tkinter.StringVar(self)
        self.typeVar.set(self.TRIGGER_TYPES[1])
        self.takeVar = tkinter.IntVar(self)
        self.clsVar = tkinter.IntVar(self)

        pxLabel = tkinter.Label(self, text="Trigger Price:")
        self.pxSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT)
        typeLabel = tkinter.Label(self, text="Trigger Type:")
        typeOption = tkinter.OptionMenu(self, self.typeVar, *self.TRIGGER_TYPES)
        typeOption.configure(**self.OPTION_PARAMS)
        takeCheck = tkinter.Checkbutton(self, var=self.takeVar,
                                        text="Take Profit")
        clsCheck = tkinter.Checkbutton(self, var=self.clsVar,
                                       text="Close on Trigger")

        pxLabel.grid(column=0, row=0)
        self.pxSpin.grid(column=1, row=0)
        typeLabel.grid(column=0, row=1)
        typeOption.grid(column=1, row=1)
        takeCheck.grid(column=0, row=2)
        clsCheck.grid(column=1, row=2)

    def get_trigger_price(self):
        """
        Returns number currently in trigger price spinbox.
        """
        return int(self.pxSpin.get())

    def get_trigger_type(self):
        """
        Returns currently selected string in trigger type menu.
        """
        return str(self.typeVar.get())

    def get_take_profit(self):
        """
        Returns if take profit is checked.
        """
        return bool(self.takeVar.get())

    def get_close_on_trigger(self):
        """
        Returns if close on trigger is checked.
        """
        return bool(self.clsVar.get())


class StopLoss(tkinter.Frame):
    """
    Frame for optional close stop order mirroring main order qantity.
    """

    TRIGGER_TYPES = [
        "Mark",
        "Last",
        "Index"
    ]
    OPTION_PARAMS = {
        "width": 9
    }

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.stopVar = tkinter.IntVar(self)
        self.typeVar = tkinter.StringVar(self)
        self.typeVar.set(self.TRIGGER_TYPES[1])

        stopCheck = tkinter.Checkbutton(self, text="Stop loss", var=self.stopVar)
        pxLabel = tkinter.Label(self, text="Trigger Price:")
        self.pxSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT)
        typeLabel = tkinter.Label(self, text="Trigger Type:")
        typeOption = tkinter.OptionMenu(self, self.typeVar, *self.TRIGGER_TYPES)
        typeOption.configure(**self.OPTION_PARAMS)

        stopCheck.grid(column=0, row=0)
        pxLabel.grid(column=0, row=1)
        self.pxSpin.grid(column=1, row=1)
        typeLabel.grid(column=0, row=2)
        typeOption.grid(column=1, row=2)

    def get_stop_loss(self):
        """
        Returns if stop loss is enabled.
        """
        return bool(self.stopVar.get())

    def get_trigger_price(self):
        """
        Returns number currently in trigger price spinbox.
        """
        return int(self.pxSpin.get())

    def get_trigger_type(self):
        """
        Returns currently selected string in trigger type menu.
        """
        return str(self.typeVar.get())
