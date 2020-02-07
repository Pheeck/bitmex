"""
Frames for landing page window.
"""

import tkinter

import backend.core as core
import backend.accounts as accounts


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

    pass
