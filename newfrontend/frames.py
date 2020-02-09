"""
Frames for landing page window.
"""

import tkinter

import backend.core as core
import backend.accounts as accounts


#
# Constants
#

SPINBOX_LIMIT = 1000000000


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


class Accounts(tkinter.Frame):  # TODO More opened windows update limit
    """
    Frame displaying wallet ballance and unrealised PnL for each account.
    """

    REQUESTS_PER_MINUTE = 25  # Window will try to respect this number
    REQUESTS_FASTER = 55
    MIN_DOTS = 1
    MAX_DOTS = 5
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    VAR = (
        "availableMargin",
        "unrealisedPnl"
    )
    TEXT = (
        "Available Margin",
        "Unrealised PnL"
    )
    WIDTH = (
        200,
        200
    )

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.fastVar = tkinter.IntVar(self)

        self.tree = tkinter.ttk.Treeview(self, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(self)
        button = tkinter.Button(subframe, text="Update",
                                command=lambda: self.update_positions())
        check = tkinter.Checkbutton(subframe, var=self.fastVar,
                                    text="Update faster (should be logged in "
                                    + "browser client for BitMEX to allow more "
                                    + "frequent requests)")
        self.label = tkinter.Label(self)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Account", anchor=tkinter.W)
        self.tree.column("#0", width=80)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        button.grid(column=0, row=0)
        check.grid(column=1, row=0)
        self.tree.pack()
        subframe.pack()
        self.label.pack()

        self._job = None
        self.dots = self.MIN_DOTS
        self.delay_multiplier = 1  # Will be set higher when request fails

        self.update_positions()

    def update_positions(self):
        """
        Query backend for all accounts margin stats, place them into treeview.
        Sets this function to repeat after UPDATE_SECONDS seconds.
        """

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Get all acount names
        names = [x["name"] for x in accounts.get_all()]

        # Get info
        success = False
        try:
            accs = core.account_margin_stats(names)
            success = True
            self.delay_multiplier = 1  # Reset to normal value
        except Exception as e:
            print(str(e))
            self.delay_multiplier += 1
        if success:
            # Fill tree
            accs.sort(key=lambda x: x["name"], reverse=False)  # Sort
            for account in accs:
                name = account["name"]
                stats = account["stats"]

                values = []
                for v in self.VAR:
                    values.append(str(stats[v]))

                self.tree.insert("", "end", text=name,
                                 values=values)
            # Resize tree
            new_height = len(self.tree.get_children())
            if new_height < self.MIN_TREE_HEIGHT:
                new_height = self.MIN_TREE_HEIGHT
            if new_height > self.MAX_TREE_HEIGHT:
                new_height = self.MAX_TREE_HEIGHT
            self.tree.configure(height=new_height)
            self.tree.pack()

            # Update dots
            self.dots += 1
            if self.dots > self.MAX_DOTS:
                self.dots = self.MIN_DOTS
            self.label.configure(text="." * self.dots)
        else:  # On error
            self.label.configure(text="Error: Wasn't able to retrieve accounts"
                                      + " info. Retrying...")

        # Set repeat
        if not self._job is None:
            self.after_cancel(self._job)
        if self.fastVar.get():
            delay = int(1000 * (60 * len(names) / self.REQUESTS_FASTER))
        else:
            delay = int(1000 * (60 * len(names) / self.REQUESTS_PER_MINUTE))
        delay *= self.delay_multiplier
        self._job = self.after(delay, self.update_positions)


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
        "entryPrice",
        "markPrice",
        "leverage",
        "unrealisedPnl",
        "roePcnt",
        "realisedPnl"
    )
    TEXT = (
        "Size",
        "Entry Price",
        "Mark Price",
        "Leverage",
        "Unrealised PNL",
        "ROE %",
        "Realised PNL"
    )
    WIDTH = (
        40,
        100,
        100,
        80,
        120,
        60,
        110
    )

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.fastVar = tkinter.IntVar(self)

        self.tree = tkinter.ttk.Treeview(self, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(self)
        button = tkinter.Button(subframe, text="Update",
                                command=lambda: self.update_positions())
        check = tkinter.Checkbutton(subframe, var=self.fastVar,
                                    text="Update faster (should be logged in "
                                    + "browser client for BitMEX to allow more "
                                    + "frequent requests)")
        self.label = tkinter.Label(self)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Symbol", anchor=tkinter.W)
        self.tree.column("#0", width=80)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        button.grid(column=0, row=0)
        check.grid(column=1, row=0)
        self.tree.pack()
        subframe.pack()
        self.label.pack()

        self._job = None
        self.dots = self.MIN_DOTS
        self.delay_multiplier = 1  # Will be set higher when request fails

        self.update_positions()

    def update_positions(self):
        """
        Query backend for currently open positions and place them into treeview.
        Sets this function to repeat after UPDATE_SECONDS seconds.
        """

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Get all acount names
        names = [x["name"] for x in accounts.get_all()]

        # Get info
        success = False
        try:
            accs = core.position_info(names)
            success = True
            self.delay_multiplier = 1  # Reset to normal value
        except Exception as e:
            print(str(e))
            self.delay_multiplier += 1
        if success:
            # Fill tree
            for account in accs:
                name = account["name"]
                positions = account["positions"]
                positions.sort(key=lambda x: x["symbol"], reverse=False)  # Sort

                parent = self.tree.insert("", "end", text=name,
                                          values=["" for x in self.VAR])

                for position in positions:
                    values = []
                    for v in self.VAR:
                        values.append(str(position[v]))

                    #self.tree.insert(parent, "end", text=position["symbol"],
                    #                 values=values)
                    self.tree.insert("", "end", text=position["symbol"],
                                     values=values)
            # Resize tree
            new_height = len(self.tree.get_children())
            if new_height < self.MIN_TREE_HEIGHT:
                new_height = self.MIN_TREE_HEIGHT
            if new_height > self.MAX_TREE_HEIGHT:
                new_height = self.MAX_TREE_HEIGHT
            self.tree.configure(height=new_height)
            self.tree.pack()

            # Update dots
            self.dots += 1
            if self.dots > self.MAX_DOTS:
                self.dots = self.MIN_DOTS
            self.label.configure(text="." * self.dots)
        else:  # On error
            self.label.configure(text="Error: Wasn't able to retrieve positions"
                                      + " info. Retrying...")

        # Set repeat
        if not self._job is None:
            self.after_cancel(self._job)
        if self.fastVar.get():
            delay = int(1000 * (60 * len(names) / self.REQUESTS_FASTER))
        else:
            delay = int(1000 * (60 * len(names) / self.REQUESTS_PER_MINUTE))
        delay *= self.delay_multiplier
        self._job = self.after(delay, self.update_positions)


class Order(tkinter.Frame):
    """
    Frame for creating new orders.
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
    LABEL_PARAMS = {
        "width": 10
    }

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

        self.accFrame = tkinter.Frame(self)
        self.mainFrame = tkinter.Frame(self)
        self.buttonFrame = tkinter.Frame(self)

        self._init_acc()
        self._init_main()
        self._init_button()

        self.accFrame.pack()
        self.mainFrame.pack()
        self.buttonFrame.pack()

        self.isAlive = True

    def _init_acc(self):
        """
        Initiate accounts frame. Internal method.
        """
        leftFrame = tkinter.Frame(self.accFrame)
        rightFrame = tkinter.Frame(self.accFrame)

        label = tkinter.Label(leftFrame, text="Select Accounts:")
        label.pack()

        self.accFrame.names = []
        self.accFrame.vars = []

        for i, account in enumerate(accounts.get_all()):
            name = account["name"]
            var = tkinter.IntVar(self.accFrame)

            check = tkinter.Checkbutton(rightFrame, text=name, var=var)
            check.grid(column=i, row=0)

            self.accFrame.names.append(name)
            self.accFrame.vars.append(var)

        leftFrame.grid(column=0, row=0)
        rightFrame.grid(column=1, row=0)

    def _init_main(self):
        """
        Initiate main frame. Internal method.
        """
        # Backend
        try:
            openInstruments = core.open_instruments(accounts.get_all()[0]["name"])
            openInstruments.sort()
        except Exception as e:
            print(e)
            openInstruments = []

        # Frontend
        self.symbolVar = tkinter.StringVar(self.mainFrame)

        symbolLabel = tkinter.Label(self.mainFrame, text="Symbol",
                                    **self.LABEL_PARAMS)
        qtyLabel = tkinter.Label(self.mainFrame, text="Quantity",
                                 **self.LABEL_PARAMS)
        levLabel = tkinter.Label(self.mainFrame, text="Leverage",
                                 **self.LABEL_PARAMS)
        pxLabel = tkinter.Label(self.mainFrame, text="Limit Price",
                                **self.LABEL_PARAMS)
        pctLabel = tkinter.Label(self.mainFrame, text="%",
                                 **self.LABEL_PARAMS)
        entryLabel = tkinter.Label(self.mainFrame, text="Entry Price",
                                   **self.LABEL_PARAMS)
        exitLabel = tkinter.Label(self.mainFrame, text="Exit Price",
                                  **self.LABEL_PARAMS)
        stopLabel = tkinter.Label(self.mainFrame, text="Stop Price",
                                  **self.LABEL_PARAMS)

        symbolCombo = tkinter.ttk.Combobox(self.mainFrame, textvariable=self.symbolVar,
                                           **self.COMBO_PARAMS)
        symbolCombo["values"] = openInstruments
        self.qtySpin = tkinter.Spinbox(self.mainFrame, from_=1, to=SPINBOX_LIMIT,
                                       **self.SPINBOX_PARAMS)
        self.levSpin = tkinter.Spinbox(self.mainFrame, from_=0, to=1000,
                                       **self.SPINBOX_PARAMS)
        self.pxSpin = tkinter.Spinbox(self.mainFrame, from_=1, to=SPINBOX_LIMIT,
                                      **self.SPINBOX_PARAMS)
        self.entryLabel = tkinter.Label(self.mainFrame, text="0")
        self.exitLabel = tkinter.Label(self.mainFrame, text="0")
        self.stopSpin = tkinter.Spinbox(self.mainFrame, from_=1, to=SPINBOX_LIMIT,
                                        **self.SPINBOX_PARAMS)

        symbolLabel.grid(column=0, row=0)
        qtyLabel.grid(column=1, row=0)
        levLabel.grid(column=2, row=0)
        pxLabel.grid(column=3, row=0)
        entryLabel.grid(column=4, row=0)
        exitLabel.grid(column=5, row=0)
        stopLabel.grid(column=6, row=0)

        symbolCombo.grid(column=0, row=1)
        self.qtySpin.grid(column=1, row=1)
        #self.levSpin.grid(column=2, row=1)
        self.pxSpin.grid(column=3, row=1)
        #self.entryLabel.grid(column=4, row=1)
        #self.exitLabel.grid(column=5, row=1)
        self.stopSpin.grid(column=6, row=1)

    def _init_button(self):
        """
        Initiate button frame. Internal method.
        """
        buyButton = tkinter.Button(self.buttonFrame, text="Buy/Long",
                                   command=lambda: window._send(sell=False),
                                   **self.BUTTON_PARAMS)
        sellButton = tkinter.Button(self.buttonFrame, text="Sell/Short",
                                    command=lambda: window._send(sell=True),
                                    **self.BUTTON_PARAMS)

        buyButton.grid(column=0, row=0)
        sellButton.grid(column=1, row=0)

    def send(self, sell=False):  # TODO
        """
        Recognize, which kind of order to send and send it.
        """
        pass

    def _send(self, function, sell=False):
        """
        Wrapper for send methods with try-catch and checking if any accounts
        are acually selected. Internal method.
        """
        names = self.accFrame.get_names()
        if not names:
            tkinter.messagebox.showerror("Error", "No accounts are selected.")
            raise BitmexGUIException("No accounts are selected.")
        try:
            self.send(sell)
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))
            raise e

    def _send_market(self, sell=False):  # TODO (btw, triggery asi zatim ne)
        """
        Query api to send market order. Internal method.
        """
        pass

    def send_limit(self, sell=False):  # TODO
        """
        Query api to send limit order. Internal method.
        """
        pass

    def send_relative(self, sell=False):  # TODO
        """
        Query api to send relative order. Internal method.
        """
        pass

    def quit(self):
        """
        Cleans up and kills the window.
        """
        self.isAlive = False
        self.after(DESTROY_DELAY, self.destroy)
