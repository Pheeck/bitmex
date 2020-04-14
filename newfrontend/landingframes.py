"""
Frames for landing page window.
"""

import tkinter
import tkinter.ttk

import backend.core as core
import backend.accounts as accounts

from backend.exceptions import BitmexGUIException

import bot.log
import bot.bot

from bot.thread import run_bot, stop_bot


#
# Constants
#

SPINBOX_LIMIT = 1000000000
RETRY_DELAY = 9000  # Standard delay before trying to request crucial data again


#
# Utility frame classes
#

class AccountsSelect(tkinter.Frame):
    """
    Frame for choosing to which accounts should new order be sent.
    """

    def __init__(self, *args, **kwargs):
        tkinter.Frame.__init__(self, *args, **kwargs)

        leftFrame = tkinter.Frame(self)
        rightFrame = tkinter.Frame(self)

        label = tkinter.Label(leftFrame, text="Select Accounts:")
        label.pack()
        self.names = []
        self.vars = []

        for i, account in enumerate(accounts.get_all()):
            name = account["name"]
            var = tkinter.IntVar(self)

            check = tkinter.Checkbutton(rightFrame, text=name, var=var)
            check.grid(column=i, row=0)

            self.names.append(name)
            self.vars.append(var)

        leftFrame.grid(column=0, row=0)
        rightFrame.grid(column=1, row=0)

    def get_names(self):
        """
        Returns currently selected account names.
        """
        result = []
        for name, var in zip(self.names, self.vars):
            if var.get():
                result.append(str(name))
        return result


#
# Landing page frame classes
#


class Overview(tkinter.Frame):
    """
    Frame displaying current global BitMEX statistics.
    """

    pass


class Accounts(tkinter.Frame):  # TODO More opened windows update limit
    """
    Frame displaying wallet ballance and unrealised PnL for each account.
    """

    TITLE = "Accounts overview"

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

    def __init__(self, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, *args, text=self.TITLE, **kwargs)

        self.fastVar = tkinter.IntVar(self)

        self.tree = tkinter.ttk.Treeview(self, height=self.MIN_TREE_HEIGHT)
        rightframe = tkinter.Frame(self)
        button = tkinter.Button(rightframe, text="Update",
                                command=lambda: self.update_positions())
        check = tkinter.Checkbutton(rightframe, var=self.fastVar,
                                    text="Update faster")
        self.label = tkinter.Label(self)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Account", anchor=tkinter.W)
        self.tree.column("#0", width=200)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        button.grid(column=0, row=0, sticky=tkinter.N+tkinter.S+tkinter.W+tkinter.E)
        check.grid(column=0, row=1)
        self.label.grid(column=0, row=1)
        self.tree.grid(column=0, row=0)
        # rightframe.grid(column=1, row=0, sticky=tkinter.N+tkinter.S+tkinter.W+tkinter.E)

        self._job = None
        self.dots = self.MIN_DOTS
        self.delay_multiplier = 1  # Will be set higher when request fails

        self.update_margin()

    def update_margin(self):
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
            self.tree.grid(column=0, row=0)

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
        self._job = self.after(delay, self.update_margin)


class Positions(tkinter.Frame):
    """
    Frame for monitoring status of open positions for each account.
    """

    TITLE = "Open positions"

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

    def __init__(self, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, *args, text=self.TITLE, **kwargs)

        self.fastVar = tkinter.IntVar(self)

        self.tree = tkinter.ttk.Treeview(self, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(self)
        button = tkinter.Button(subframe, text="Update",
                                command=lambda: self.update_positions())
        check = tkinter.Checkbutton(subframe, var=self.fastVar,
                                    text="Update faster")
        label = tkinter.Label(subframe, text="Double-click a position to close it")
        self.label = tkinter.Label(self)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Symbol", anchor=tkinter.W)
        self.tree.column("#0", width=100)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        # Handle closing positions
        self.tree.bind("<Double-1>", self.close_selected)

        label.grid(column=0, row=0)
        button.grid(column=1, row=0)
        check.grid(column=2, row=0)
        self.tree.pack()
        #subframe.pack()
        self.label.pack()

        self._job = None
        self.dots = self.MIN_DOTS
        self.delay_multiplier = 1  # Will be set higher when request fails

        self.update_accounts()
        self.update_positions()

    def close_selected(self, event):
        """
        Get information about currently selected item in treeview and query
        backend to send adequate close position order.
        """
        try:
            # Get information from treeview
            currItem = self.tree.focus()
            parent = self.tree.parent(currItem)
            if not parent:
                return  # This is account node, not position node
            currData = self.tree.item(currItem)
            parData = self.tree.item(parent)

            symbol = currData["text"]
            accName = parData["text"]
            quantity = float(currData["values"][self.VAR.index("size")])
            sell = not quantity < 0  # Should be opposite of position polarity
            quantity = abs(quantity)
        except Exception as e:
            tkinter.messagebox.showerror("Error closing position",
                                         str(e))
            raise e
        if not symbol:
            tkinter.messagebox.showerror("Error closing position",
                                         "Blank symbol")
            raise BitmexGUIException("Error closing position: Blank symbol")
        if not accName:
            tkinter.messagebox.showerror("Error closing position",
                                         "No account name")
            raise BitmexGUIException("Error closing position: No account name")

        # Confirm close position
        if tkinter.messagebox.askokcancel("Confirm close position",
                                          ("Do you wish to close position %s " +
                                          "belonging to account '%s'?") %
                                          (symbol, accName)):
            # Send order
            core.order_market([accName], symbol, quantity, sell)

    def update_accounts(self):
        """
        Query backend for account list and place them into treeview.
        Completely clears tree beforehand.
        """

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Get all acount names
        names = [x["name"] for x in accounts.get_all()]

        # Fill tree
        for name in names:
            item = self.tree.insert("", "end", text=name, open=False,
                                    values=["" for x in self.VAR])

        self._resize_tree()

    def update_positions(self):
        """
        Query backend for currently open positions and place them into treeview.
        Sets this function to repeat after UPDATE_SECONDS seconds.
        Requires tree to already be populated with accounts.
        Clears positions from tree beforehand.
        """

        # Clear positions from tree
        for child in self.tree.get_children():
            positions = self.tree.get_children(child)
            if positions:
                self.tree.delete(positions)

        # Get all acount names alredy in treeview
        names = []
        for child in self.tree.get_children():
            names.append(self.tree.item(child)["text"])

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
            for account, parent in zip(accs, self.tree.get_children()):
                name = account["name"]
                positions = account["positions"]
                positions.sort(key=lambda x: x["symbol"], reverse=False)  # Sort

                for position in positions:
                    values = []
                    for v in self.VAR:
                        values.append(str(position[v]))

                    self.tree.insert(parent, "end", text=position["symbol"],
                                     values=values)
            self._resize_tree()

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

    def _resize_tree(self):
        """
        Internal method
        """
        new_height = len(self.tree.get_children())
        if new_height < self.MIN_TREE_HEIGHT:
            new_height = self.MIN_TREE_HEIGHT
        if new_height > self.MAX_TREE_HEIGHT:
            new_height = self.MAX_TREE_HEIGHT
        self.tree.configure(height=new_height)
        self.tree.pack()


class Order(tkinter.Frame):
    """
    Frame for creating new orders.
    """

    TITLE = "New order"

    TRIGGER_TYPE = "Last"


    class Main(tkinter.Frame):
        """
        Frame for specifying details of new order.
        """

        COMBO_PARAMS = {
            "width": 9
        }
        SPINBOX_PARAMS = {
            "width": 9
        }
        LABEL_PARAMS = {
            "width": 12
        }
        PRIORITY_SYMBOLS = (
            "XBTUSD",
            "ETHUSD"
        )
        DEFAULT_PX = 10000

        def __init__(self, *args, **kwargs):
            tkinter.Frame.__init__(self, *args, **kwargs)

            # Frontend
            self.symbolVar = tkinter.StringVar(self)
            self.limitVar = tkinter.IntVar(self)
            self.stopVar = tkinter.IntVar(self)

            self.limitVar.set(1)
            self.stopVar.set(1)

            symbolLabel = tkinter.Label(self, text="Symbol",
                                        **self.LABEL_PARAMS)
            qtyLabel = tkinter.Label(self, text="Quantity",
                                     **self.LABEL_PARAMS)
            levLabel = tkinter.Label(self, text="Leverage",
                                     **self.LABEL_PARAMS)
            pxLabel = tkinter.Checkbutton(self, text="Limit Price",
                                          var=self.limitVar,  # dirty hack ahead
                                          command=lambda: self.pxSpin.configure(
                                            state=\
                                            tkinter.NORMAL if self.limitVar.get()
                                            else tkinter.DISABLED
                                          ),  # end of dirty hack
                                          **self.LABEL_PARAMS)
            pctLabel = tkinter.Label(self, text="%",
                                     **self.LABEL_PARAMS)
            entryLabel = tkinter.Label(self, text="Entry Price",
                                       **self.LABEL_PARAMS)
            exitLabel = tkinter.Label(self, text="Exit Price",
                                      **self.LABEL_PARAMS)
            stopLabel = tkinter.Checkbutton(self, text="Stop Price",
                                            var=self.stopVar,  # dirty hack ahead
                                            command=lambda: self.stopSpin.configure(
                                              state=\
                                              tkinter.NORMAL if self.stopVar.get()
                                              else tkinter.DISABLED
                                            ),  # end of dirty hack
                                            **self.LABEL_PARAMS)

            self.symbolCombo = tkinter.ttk.Combobox(self, textvariable=self.symbolVar,
                                                    **self.COMBO_PARAMS)
            self.qtySpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT,
                                           **self.SPINBOX_PARAMS)
            self.levSpin = tkinter.Spinbox(self, from_=0, to=1000,
                                           state=tkinter.DISABLED,
                                           **self.SPINBOX_PARAMS)
            self.pxSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT,
                                          **self.SPINBOX_PARAMS)
            self.entryLabel = tkinter.Label(self, text="0", state=tkinter.DISABLED)
            self.exitLabel = tkinter.Label(self, text="0", state=tkinter.DISABLED)
            self.stopSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT,
                                            **self.SPINBOX_PARAMS)

            self.pxSpin.delete(0)
            self.pxSpin.insert(0, self.DEFAULT_PX)
            self.stopSpin.delete(0)
            self.stopSpin.insert(0, self.DEFAULT_PX)

            # Backend
            self._fetch_instruments()

            # Frontend again
            symbolLabel.grid(column=0, row=0)
            qtyLabel.grid(column=1, row=0)
            levLabel.grid(column=2, row=0)
            pxLabel.grid(column=3, row=0)
            entryLabel.grid(column=4, row=0)
            exitLabel.grid(column=5, row=0)
            stopLabel.grid(column=6, row=0)

            self.symbolCombo.grid(column=0, row=1)
            self.qtySpin.grid(column=1, row=1)
            self.levSpin.grid(column=2, row=1)
            self.pxSpin.grid(column=3, row=1)
            self.entryLabel.grid(column=4, row=1)
            self.exitLabel.grid(column=5, row=1)
            self.stopSpin.grid(column=6, row=1)

        def _fetch_instruments(self):
            """
            Request list of open instruments from api.
            Then populate this frame's symbol combobox with it.

            Will schedule itself to repeat if fetch fails.
            Internal method
            """
            try:
                openInstruments = core.open_instruments(accounts.get_all()[0]["name"])
                openInstruments.sort()
            except IndexError:
                print("Warning: No accounts were created yet.")
                openInstruments = []
            except Exception as e:
                print(e)
                openInstruments = []

            # Schedule repeat if no openInstrumets
            if not openInstruments:
                self.after(RETRY_DELAY, self._fetch_instruments)
                print("Warning: Failed to fetch open instruments. Retrying...")
                return

            # Priority symbols at top of list if they exist
            for symbol in self.PRIORITY_SYMBOLS[::-1]:
                if symbol in openInstruments:
                    openInstruments.remove(symbol)
                    openInstruments.insert(0, symbol)

            # Set first instrument as selected
            self.symbolVar.set(openInstruments[0])

            # Populate combobox
            self.symbolCombo["values"] = openInstruments

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

        def get_limit(self):
            """
            Returns whether limit checkbox is checked.
            """
            return bool(self.limitVar.get())

        def get_px(self):
            """
            Returns current number in limit price spinbox.
            """
            return float(self.pxSpin.get())

        def get_stop(self):
            """
            Returns whether stop checkbox is checked.
            """
            return bool(self.stopVar.get())

        def get_stop_px(self):
            """
            Returns current number in stop price spinbox.
            """
            return float(self.stopSpin.get())


    class Buttons(tkinter.Frame):
        """
        Frame with buy and sell buttons. Used to send new order.
        """

        BUTTON_PARAMS = {
            "width": 15
        }

        def __init__(self, parent, *args, **kwargs):
            tkinter.Frame.__init__(self, parent, *args, **kwargs)

            buyButton = tkinter.Button(self, text="Buy/Long",
                                       command=lambda: parent._send(sell=False),
                                       **self.BUTTON_PARAMS)
            sellButton = tkinter.Button(self, text="Sell/Short",
                                        command=lambda: parent._send(sell=True),
                                        **self.BUTTON_PARAMS)

            buyButton.grid(column=0, row=0)
            sellButton.grid(column=1, row=0)


    def __init__(self, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, *args, text=self.TITLE, **kwargs)

        self.accFrame = AccountsSelect(self)
        self.mainFrame = self.Main(self)
        self.buttonFrame = self.Buttons(self)

        self.accFrame.pack(fill=tkinter.X)
        self.mainFrame.pack()
        self.buttonFrame.pack()

        self.update_accounts()

    def update_accounts(self):
        """
        Query backend for logged in accounts and adjust ui adequately.
        """
        self.accFrame.destroy()
        self.mainFrame.pack_forget()
        self.buttonFrame.pack_forget()

        self.accFrame = AccountsSelect(self)

        self.accFrame.pack(fill=tkinter.X)
        self.mainFrame.pack()
        self.buttonFrame.pack()

    def send(self, sell=False):
        """
        Recognize, which kind of order to send and send it.
        """
        if self.mainFrame.get_limit():
            self.send_limit(sell)
        else:
            self.send_market(sell)

    def _send(self, sell=False):
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

    def send_market(self, sell=False):
        """
        Query api to send market order. Use parameters inputed by user.
        """
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        # Handle stop loss
        stopLoss = self.mainFrame.get_stop()
        stopLossParams = {}
        if stopLoss:
            stopLossParams["stopPrice"] = self.mainFrame.get_stop_px()
            stopLossParams["trigger"] = self.TRIGGER_TYPE
        # Send order
        core.order_market(accountNames, symbol, quantity, sell, stopLoss=stopLoss,
                          **stopLossParams)

    def send_limit(self, sell=False):
        """
        Query api to send limit order. Use parameters inputed by user.
        """
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        limitPrice = self.mainFrame.get_px()
        # Handle stop loss
        stopLoss = self.mainFrame.get_stop()
        stopLossParams = {}
        if stopLoss:
            stopLossParams["stopPrice"] = self.mainFrame.get_stop_px()
            stopLossParams["trigger"] = self.TRIGGER_TYPE
        # Send order
        core.order_limit(accountNames, symbol, quantity, limitPrice, sell,
                         stopLoss=stopLoss, **stopLossParams)

    def send_relative(self, sell=False):  # TODO
        """
        Query api to send relative order. Use parameters inputed by user.
        """
        pass


class Bot(tkinter.Frame):
    """
    Frame for monitoring what bot does.
    Also used to turn bot on/off.
    """

    TITLE = "Bot"

    UPDATE_SECONDS = 1

    TEXT_OFF = "Start bot"
    TEXT_ON = "Stop bot"

    SHOW_LOG_ENTRIES = 10

    TREE_HEIGHT = 10
    VAR = (
        "contract1",
        "price1",
        "contract2",
        "price2",
        "difference",
    )
    TEXT = (
        "First contract",
        "Price",
        "Second contract",
        "Price",
        "Delta",
    )
    WIDTH = (
        130,
        60,
        130,
        60,
        60,
    )

    def __init__(self, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, *args, text=self.TITLE, **kwargs)

        self.runVar = tkinter.IntVar(self)
        self.runVar.set(0)
        self.accountVar = tkinter.StringVar(self)

        runFrame = tkinter.Frame(self)
        self.runButton = tkinter.Button(runFrame, text=self.TEXT_OFF,
                                        command=self.toggle_running)
        self.accountsCombo = tkinter.ttk.Combobox(runFrame, text="",
                                                  textvariable=self.accountVar)
        self.tree = tkinter.ttk.Treeview(self, height=self.TREE_HEIGHT)
        self.label = tkinter.Label(self, text="")

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Log", anchor=tkinter.W)
        self.tree.column("#0", width=170)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        self.accountsCombo.grid(column=0, row=0)
        self.runButton.grid(column=1, row=0)
        runFrame.pack()
        self.tree.pack()
        self.label.pack()

        self._job = None

        self._bot_thread = None

        self.update_accounts()
        self.update_values()

    def update_accounts(self):
        """
        Query backend for logged in accounts and adjust ui adequately.
        """
        names = [account["name"] for account in accounts.get_all()]
        self.accountsCombo["values"] = names
        if self.accountVar.get() in names:
            bot.settings.set_account(self.accountVar.get())
        elif bot.settings.get_account() in names:
            self.accountVar.set(bot.settings.get_account())
        else:
            self.accountVar.set(names[0])
            bot.settings.set_account(names[0])

    def update_values(self):
        """
        Query bot backend for log entries and place them into treeview.
        Sets this function to repeat after UPDATE_SECONDS seconds.
        Clears positions from tree beforehand.
        Doesnt run if no new entries were written since last call to this.
        """
        if bot.bot.has_new_entry():
            entries = bot.log.read_entries(self.SHOW_LOG_ENTRIES)
            entries = entries[::-1]  # Reverse order of entries to be displayed

            # Clear tree
            for child in self.tree.get_children():
                self.tree.delete(child)

            # Fill tree
            for entry in entries:
                time = entry.pop("time")
                values = []
                for v in self.VAR:
                    values.append(str(entry[v]))
                self.tree.insert("", "end", text=time, values=values)

        # Update seconds
        if self.runVar.get():  # If bot running
            seconds = bot.bot.get_seconds()
            self.label.configure(text = str(seconds) + " seconds remaining")
        else:
            self.label.configure(text="")

        # Set repeat
        if self.runVar.get():  # Repeat only if bot is running
            if not self._job is None:
                self.after_cancel(self._job)
            delay = 1000 * self.UPDATE_SECONDS
            self._job = self.after(delay, self.update_values)

    def toggle_running(self):
        """
        Switches between on and off states of bot.
        """
        if self.runVar.get():  # If bot running
            # Bot backend
            stop_bot(self._bot_thread)
            # Frontend
            self.runVar.set(0)
            self.runButton.configure(text=self.TEXT_OFF)
            self.accountsCombo.configure(state="enabled")
        else:
            # Bot backend
            bot.settings.set_account(self.accountVar.get())
            self._bot_thread = run_bot()
            # Frontend
            self.runVar.set(1)
            self.runButton.configure(text=self.TEXT_ON)
            self.accountsCombo.configure(state="disabled")

            self.after(500, self.update_values)

    def is_running(self):
        """
        Returns if bot is currently runnning.
        """
        return bool(self.runVar.get())
