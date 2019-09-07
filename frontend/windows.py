"""
Frontend window classes.
"""

import tkinter
import tkinter.messagebox
import tkinter.ttk

import frontend.orderframes as orderframes

import backend.accounts as accounts
import backend.core as core
from backend.exceptions import BitmexAccountsException, BitmexGUIException

from utility import significant_figures


#
# Constants
#


DESTROY_DELAY = 200  # Delay before window destroys itself at quit() method call
SPINBOX_LIMIT = 1000000000


#
# Classes
#

# Main window

class Main(tkinter.Tk):
    """
    Main window of the program.
    """

    TITLE = "BitMEX Assistant"
    BUTTON_PARAMS = {
        "width": 18
    }

    def __init__(self, *args, **kvargs):
        tkinter.Tk.__init__(self, *args, **kvargs)

        # Backend
        try:
            accounts.load()
        except BitmexAccountsException:
            print("No accounts savefile found, creating a blank one now...")
            accounts.save()
            accounts.load()

        # Frontend
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.wm_title(self.TITLE)

        # Child windows
        posWindow = Positions(hidden=True)
        insWindow = Instruments(hidden=True)
        ordsWindow = ActiveOrders(hidden=True)
        stpsWindow = StopOrders(hidden=True)
        histWindow = OrderHistory(hidden=True)
        accWindow = AccountManagement(hidden=True)
        newWindow = SelectOrder(hidden=True)
        calcWindow = Calculator(hidden=True)

        self.windows = [
            posWindow,
            insWindow,
            ordsWindow,
            stpsWindow,
            accWindow,
            newWindow,
            calcWindow
        ]

        # Widgets
        frame = tkinter.Frame(self)
        posButton = tkinter.Button(frame,
                                   text="Positions",
                                   command=lambda: posWindow.toggle_hidden(),
                                   **self.BUTTON_PARAMS)
        insButton = tkinter.Button(frame,
                                   text="Instruments",
                                   command=lambda: insWindow.toggle_hidden(),
                                   **self.BUTTON_PARAMS)
        ordsButton = tkinter.Button(frame,
                                    text="Active Orders",
                                    command=lambda: ordsWindow.toggle_hidden(),
                                    **self.BUTTON_PARAMS)
        stpsButton = tkinter.Button(frame,
                                    text="Stop Orders",
                                    command=lambda: stpsWindow.toggle_hidden(),
                                    **self.BUTTON_PARAMS)
        histButton = tkinter.Button(frame,
                                    text="Order History",
                                    command=lambda: histWindow.toggle_hidden(),
                                    **self.BUTTON_PARAMS)
        accButton = tkinter.Button(frame,
                                   text="Account Management",
                                   command=lambda: accWindow.toggle_hidden(),
                                   **self.BUTTON_PARAMS)
        newButton = tkinter.Button(frame,
                                   text="New Order",
                                   command=lambda: newWindow.toggle_hidden(),
                                   **self.BUTTON_PARAMS)
        calcButton = tkinter.Button(frame,
                                    text="PNL Calculator",
                                    command=lambda: calcWindow.toggle_hidden(),
                                    **self.BUTTON_PARAMS)
        hideButton = tkinter.Button(frame,
                                    text="Hide All Windows",
                                    command=lambda: [x.hide() for x in self.windows],
                                    **self.BUTTON_PARAMS)
        showButton = tkinter.Button(frame,
                                    text="Show All Windows",
                                    command=lambda: [x.show() for x in self.windows],
                                    **self.BUTTON_PARAMS)

        posButton.grid(row=0, column=0)
        insButton.grid(row=0, column=1)
        ordsButton.grid(row=1, column=0)
        stpsButton.grid(row=1, column=1)
        histButton.grid(row=2, column=0)
        accButton.grid(row=2, column=1)
        newButton.grid(row=3, column=0)
        calcButton.grid(row=3, column=1)
        hideButton.grid(row=4, column=0)
        showButton.grid(row=4, column=1)
        frame.pack()

        # Alive flag
        self.isAlive = True

    def update(self, *args, **kvargs):
        """
        Overriding update method to also update child windows.
        """
        for window in self.windows:
            window.update()
        tkinter.Tk.update(self, *args, **kvargs)

    def quit(self):
        """
        Cleans up and kills the program.
        """
        accounts.save()
        self.isAlive = False
        self.after(DESTROY_DELAY, self.destroy)


# Orders

class AbstractOrder(tkinter.Tk):
    """
    Abstract class. Only for inheriting.

    Super of all order windows. Has main frame and account frame. send() method
    is supposed to be overridden. Supports isAlive.
    """

    TITLE = ""

    def __init__(self, *args, **kvargs):
        tkinter.Tk.__init__(self, *args, **kvargs)

        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.wm_title(self.TITLE)

        masterFrame = tkinter.Frame(self)
        self.leftFrame = tkinter.Frame(masterFrame)
        self.rightFrame = tkinter.Frame(masterFrame)
        self.mainFrame = orderframes.Main(self.leftFrame, window=self)
        self.accFrame = orderframes.Accounts(self.rightFrame)

        self.mainFrame.pack()
        self.accFrame.pack()
        self.leftFrame.grid(column=0, row=0)
        self.rightFrame.grid(column=1, row=0)
        masterFrame.pack()

        self.isAlive = True

    def _send(self, sell=False):
        """
        send() but wrapped in try-catch and checking if any accounts are acually
        selected.
        """
        names = self.accFrame.get_names()
        if not names:
            tkinter.messagebox.showerror("Error", "No accounts are selected.")
            raise BitmexGUIException("No accounts are selected.")
        try:
            self.send(sell)
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def send(self, sell=False):
        """
        Query api to send order.
        """
        pass

    def quit(self):
        """
        Cleans up and kills the window.
        """
        self.isAlive = False
        self.after(DESTROY_DELAY, self.destroy)


class Market(AbstractOrder):
    """
    Order window. Queries api to send market orders.
    """

    TITLE = "New Market Order"

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        core.order_market(accountNames, symbol, quantity, sell)


class TriggerMarket(AbstractOrder):
    """
    Order window. Queries api to send stop market orders and take profit market
    orders.
    """

    TITLE = "New Trigger Market Order"

    def __init__(self, *args, **kvargs):
        AbstractOrder.__init__(self, *args, **kvargs)

        self.triggFrame = orderframes.Trigger(self.leftFrame)
        self.triggFrame.pack()

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        triggerPrice = self.triggFrame.get_trigger_price()
        triggerType = self.triggFrame.get_trigger_type()
        closeOnTrigger = self.triggFrame.get_close_on_trigger()
        takeProfit = self.triggFrame.get_take_profit()
        if takeProfit:
            function = core.order_take_profit_market
        else:
            function = core.order_stop_market
        function(accountNames, symbol, quantity, triggerPrice, sell, triggerType,
                 closeOnTrigger)


class Limit(AbstractOrder):
    """
    Order window. Queries api to send limit orders.
    """

    TITLE = "New Limit Order"

    def __init__(self, *args, **kvargs):
        AbstractOrder.__init__(self, *args, **kvargs)

        self.limitFrame = orderframes.Limit(self.leftFrame)
        self.limitFrame.pack()

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        limitPrice = self.limitFrame.get_limit_price()
        postOnly = self.limitFrame.get_post_only()
        reduceOnly = self.limitFrame.get_reduce_only()
        if postOnly:
            core.order_limit_post_only(accountNames, symbol, quantity, limitPrice,
                                       sell, reduceOnly)
        else:
            hidden = self.limitFrame.get_hidden()
            displayQty = self.limitFrame.get_display_qty()
            timeInForce = self.limitFrame.get_time_in_force()
            core.order_limit(accountNames, symbol, quantity, limitPrice, sell,
                             hidden, displayQty, timeInForce, reduceOnly)


class TriggerLimit(Limit):
    """
    Order window. Queries api to send stop limit orders and take profit limit
    orders.
    """

    TITLE = "New Trigger Limit Order"

    def __init__(self, *args, **kvargs):
        Limit.__init__(self, *args, **kvargs)

        self.limitFrame.roCheck.configure(state="disabled")

        self.triggFrame = orderframes.Trigger(self.leftFrame)
        self.triggFrame.pack()

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        quantity = self.mainFrame.get_qty()
        limitPrice = self.limitFrame.get_limit_price()
        postOnly = self.limitFrame.get_post_only()
        triggerPrice = self.triggFrame.get_trigger_price()
        triggerType = self.triggFrame.get_trigger_type()
        closeOnTrigger = self.triggFrame.get_close_on_trigger()
        takeProfit = self.triggFrame.get_take_profit()
        if postOnly:
            if takeProfit:
                method = core.order_take_profit_limit_post_only
            else:
                method = core.order_stop_limit_post_only
            method(accountNames, symbol, quantity, limitPrice, triggerPrice,
                   sell, triggerType, closeOnTrigger)
        else:
            hidden = self.limitFrame.get_hidden()
            displayQty = self.limitFrame.get_display_qty()
            timeInForce = self.limitFrame.get_time_in_force()
            if takeProfit:
                method = core.order_take_profit_limit
            else:
                method = core.order_stop_limit
            method(accountNames, symbol, quantity, limitPrice, triggerPrice,
                   sell, triggerType, closeOnTrigger, hidden, displayQty,
                   timeInForce)


class RelativeLimit(AbstractOrder):
    """
    Order window. Queries api to send relative limit orders.
    """

    TITLE = "New Relative Limit Order"

    def __init__(self, *args, **kvargs):
        AbstractOrder.__init__(self, *args, **kvargs)

        self.mainFrame.qtyLabel.configure(text="Percent: ")
        self.mainFrame.qtySpin.configure(to=100)

        self.limitFrame = orderframes.Limit(self.leftFrame)
        self.limitFrame.pack()

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        percent = self.mainFrame.get_qty()
        limitPrice = self.limitFrame.get_limit_price()
        postOnly = self.limitFrame.get_post_only()
        reduceOnly = self.limitFrame.get_reduce_only()
        if postOnly:
            core.order_limit_relative_post_only(accountNames, symbol, percent,
                                                limitPrice, sell, reduceOnly)
        else:
            hidden = self.limitFrame.get_hidden()
            displayQty = self.limitFrame.get_display_qty()
            timeInForce = self.limitFrame.get_time_in_force()
            core.order_limit_relative(accountNames, symbol, percent, limitPrice,
                                      sell, hidden, displayQty, timeInForce,
                                      reduceOnly)


class TriggerRelativeLimit(AbstractOrder):
    """
    Order window. Queries api to send take profit relative limit orders and
    stop relative limit orders.
    """

    TITLE = "New Trigger Relative Limit Order"

    def __init__(self, *args, **kvargs):
        Limit.__init__(self, *args, **kvargs)

        self.mainFrame.qtyLabel.configure(text="Percent: ")
        self.mainFrame.qtySpin.configure(to=100)

        self.limitFrame.roCheck.configure(state="disabled")

        self.triggFrame = orderframes.Trigger(self.leftFrame)
        self.triggFrame.pack()

    def send(self, sell=False):
        accountNames = self.accFrame.get_names()
        symbol = self.mainFrame.get_symbol()
        percent = self.mainFrame.get_qty()
        limitPrice = self.limitFrame.get_limit_price()
        postOnly = self.limitFrame.get_post_only()
        triggerPrice = self.triggFrame.get_trigger_price()
        triggerType = self.triggFrame.get_trigger_type()
        closeOnTrigger = self.triggFrame.get_close_on_trigger()
        takeProfit = self.triggFrame.get_take_profit()
        if postOnly:
            if takeProfit:
                method = core.order_take_profit_limit_relative_post_only
            else:
                method = core.order_stop_limit_relative_post_only
            method(accountNames, symbol, percent, limitPrice, triggerPrice,
                   sell, triggerType, closeOnTrigger)
        else:
            hidden = self.limitFrame.get_hidden()
            displayQty = self.limitFrame.get_display_qty()
            timeInForce = self.limitFrame.get_time_in_force()
            if takeProfit:
                method = core.order_take_profit_limit_relative
            else:
                method = core.order_stop_limit_relative
            method(accountNames, symbol, percent, limitPrice, triggerPrice,
                   sell, triggerType, closeOnTrigger, hidden, displayQty,
                   timeInForce)


# Other windows

class Login(tkinter.Tk):
    """
    Window for creating new account dicts, i.e. logging in.
    """

    TITLE = "Login"

    def __init__(self, *args, **kvargs):
        tkinter.Tk.__init__(self, *args, **kvargs)

        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.wm_title(self.TITLE)

        frame = tkinter.Frame(self)
        nameLabel = tkinter.Label(frame, text="Name:")
        servLabel = tkinter.Label(frame, text="Server:")
        keyLabel = tkinter.Label(frame, text="Key:")
        secLabel = tkinter.Label(frame, text="Secret:")
        self.nameEntry = tkinter.Entry(frame)
        self.servEntry = tkinter.Entry(frame)
        self.keyEntry = tkinter.Entry(frame)
        self.secEntry = tkinter.Entry(frame)
        button = tkinter.Button(frame, text="Ok", command=self.submit)

        nameLabel.grid(column=0, row=0)
        servLabel.grid(column=0, row=1)
        keyLabel.grid(column=0, row=2)
        secLabel.grid(column=0, row=3)
        self.nameEntry.grid(column=1, row=0)
        self.servEntry.grid(column=1, row=1)
        self.keyEntry.grid(column=1, row=2)
        self.secEntry.grid(column=1, row=3)
        button.grid(column=1, row=4)
        frame.pack()

        self.isAlive = True

    def submit(self):
        """
        Query backend to create new account from data in this windows entries
        and quit this window.
        """
        name = self.nameEntry.get()
        server = self.servEntry.get()
        key = self.keyEntry.get()
        secret = self.secEntry.get()
        try:
            accounts.new(name, key, secret, server)
            # Test if account valid
            try:
                core.account_available_margin(name)
                self.quit()
            except Exception as e:
                tkinter.messagebox.showerror("Error", "Wasn't able to validate "
                                             + "the new account:\n" + str(e))
                accounts.delete(name)
        except BitmexAccountsException as e:
            tkinter.messagebox.showerror("Error", str(e))

    def quit(self):
        """
        Cleans up and kills this window.
        """
        self.isAlive = False
        self.after(DESTROY_DELAY, self.destroy)


# Child windows

class AbstractChild(tkinter.Tk):
    """
    Abstract class. Only for inheriting.

    Super of all child windows. Can be hidden and remembers its geometry.
    """

    def __init__(self, *args, hidden=True, **kvargs):
        tkinter.Tk.__init__(self, *args, **kvargs)

        self.wm_title(self.TITLE)
        self.protocol("WM_DELETE_WINDOW", self.toggle_hidden)

        self.geom_save = None
        self.hidden = hidden
        if hidden:
            self.withdraw()

    def hide(self):
        if not self.hidden:
            self.geom_save = self.geometry()
            self.withdraw()
            self.hidden = True

    def show(self):
        if self.hidden:
            self.deiconify()
            if self.geom_save is None:
                self.minsize()
            else:
                self.geometry(self.geom_save)
            self.hidden = False

    def toggle_hidden(self):
        """
        Hide or show this window.
        """
        if self.hidden:
            self.show()
        else:
            self.hide()


class AccountManagement(AbstractChild):
    """
    Window for viewing, creating and deleting accounts.
    """

    TITLE = "Account Management"

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame)
        subframe = tkinter.Frame(frame)
        newButton = tkinter.Button(subframe,
                                   text="New",
                                   command=self.new_account)
        delButton = tkinter.Button(subframe,
                                   text="Delete",
                                   command=self.delete_account)

        self.tree["columns"] = ("server", "key")
        self.tree.heading("#0", text="Name", anchor=tkinter.W)
        self.tree.heading("server", text="Server", anchor=tkinter.W)
        self.tree.heading("key", text="Key", anchor=tkinter.W)

        self.update_accounts()

        newButton.grid(column=0, row=0)
        delButton.grid(column=1, row=0)
        self.tree.pack()
        subframe.pack()
        frame.pack()

        self.login = None

    def update(self):
        """
        Overriding update method to also update login window.
        """
        if not self.login is None:
            if self.login.isAlive:
                self.login.update()
            else:  # Login window was just closed
                self.update_accounts()
                self.login = None
        AbstractChild.update(self)

    def update_accounts(self):
        """
        Query backend for loaded accounts and place them into treeview.
        """
        self.tree.delete(*self.tree.get_children())
        for account in accounts.get_all():
            self.tree.insert("", "end", text=account["name"],
                             values=(account["host"], account["key"]))

    def new_account(self):
        """
        Open login window.
        """
        if self.login is None:
            self.login = Login()

    def delete_account(self):
        """
        Query backend to delete account currently selected in treeview.
        """
        selected_iid = self.tree.focus()

        if not selected_iid:  # No item selected
            tkinter.messagebox.showerror("Error", "No item selected.")
            raise BitmexGUIException("No item selected.")

        name = self.tree.item(self.tree.focus())["text"]
        accounts.delete(name)
        self.update_accounts()


class SelectOrder(AbstractChild):
    """
    Window for choosing which type of order to create.
    """

    TITLE = "New Order Menu"
    OPTION_PARAMS = {
        "width": 30
    }
    ORDER_TYPES = [
        "Market",
        "Limit",
        "Relative Limit"
    ]
    ORDER_WINDOWS = {
        "Market": Market,
        "Limit": Limit,
        "Relative Limit": RelativeLimit
    }
    TRIGG_WINDOWS = {
        "Market": TriggerMarket,
        "Limit": TriggerLimit,
        "Relative Limit": TriggerRelativeLimit
    }

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        self.orderVar = tkinter.StringVar(self)
        self.triggVar = tkinter.IntVar(self)
        self.orderVar.set(self.ORDER_TYPES[0])

        frame = tkinter.Frame(self)
        orderOption = tkinter.OptionMenu(frame, self.orderVar,
                                         *self.ORDER_TYPES)
        orderOption.configure(self.OPTION_PARAMS)
        triggCheck = tkinter.Checkbutton(frame,
                                         text="Trigger Order",
                                         var=self.triggVar)
        button = tkinter.Button(frame,
                                text="Ok",
                                command=lambda: self.new_order())

        orderOption.pack()
        triggCheck.pack()
        button.pack()
        frame.pack()

        self.order_window = None

    def update(self):
        """
        Overriding update method to also update login window.
        """
        if not self.order_window is None and self.order_window.isAlive:
            self.order_window.update()
        AbstractChild.update(self)

    def new_order(self):
        """
        Open new order window.
        """
        if self.order_window is None or not self.order_window.isAlive:
            if self.triggVar.get():
                self.order_window = self.TRIGG_WINDOWS[self.orderVar.get()]()
            else:
                self.order_window = self.ORDER_WINDOWS[self.orderVar.get()]()


class Positions(AbstractChild):
    """
    Window for monitoring status of positions of all accounts.
    """

    TITLE = "Open Positions"
    REQUESTS_PER_MINUTE = 25  # Window will try to respect this number
    REQUESTS_FASTER = 55
    MIN_DOTS = 1
    MAX_DOTS = 5
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    VAR = (
        "size",
        "value",
        "notional",
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
        "Value",
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

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        self.fastVar = tkinter.IntVar(self)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(frame)
        button = tkinter.Button(subframe, text="Update",
                                command=lambda: self.update_positions())
        check = tkinter.Checkbutton(subframe, var=self.fastVar,
                                    text="Update faster (should be logged in "
                                    + "browser client for BitMEX to allow more "
                                    + "frequent requests)")
        self.label = tkinter.Label(frame)

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
        frame.pack()

        self._job = None
        self.dots = self.MIN_DOTS
        self.delay_multiplier = 1  # Will be set higher when request fails

    def show(self):
        """
        Overriding so that this window updates its positions when shown.
        """
        AbstractChild.show(self)
        self.update_positions()

    def update_positions(self):
        """
        Query backend for currently open positions and place them into treeview.
        Sets this function to repeat after UPDATE_SECONDS seconds.
        """
        # Stop updating if hidden
        if self.hidden:
            return

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


class Instruments(AbstractChild):
    """
    Window for listing all instruments per each account. Is able to set their
    leverage and risk limit.
    """

    TITLE = "Open Instruments"
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    TREE_HEIGHT_MULTIPLIER = 3
    VAR = (
        "leverage",
        "riskLimit",
        "realisedPnl"
    )
    TEXT = (
        "Leverage",
        "Risk Limit",
        "Realised PNL"
    )

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame, height=self.MIN_TREE_HEIGHT)
        updateButton = tkinter.Button(frame,
                                      text="Update",
                                      command=self.update_instruments)
        subframe = tkinter.Frame(frame)
        self.levSpin = tkinter.Spinbox(subframe, from_=0, to=1000)
        levButton = tkinter.Button(subframe,
                                   text="Set Leverage",
                                   command=self.set_leverage)
        self.riskSpin = tkinter.Spinbox(subframe, from_=1, to=11000)
        riskButton = tkinter.Button(subframe,
                                    text="Set Risk Limit",
                                    command=self.set_risk_limit)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Symbol", anchor=tkinter.W)
        for v, t in zip(self.VAR, self.TEXT):
            self.tree.heading(v, text=t, anchor=tkinter.W)

        self.levSpin.grid(column=0, row=0)
        levButton.grid(column=1, row=0)
        self.riskSpin.grid(column=0, row=1)
        riskButton.grid(column=1, row=1)
        self.tree.pack()
        updateButton.pack()
        subframe.pack()
        frame.pack()

    def _get_selected(self):
        """
        Returns tupple of currently selected (account name, symbol).
        """
        selected_iid = self.tree.focus()
        parent_iid = self.tree.parent(selected_iid)
        selected = self.tree.item(selected_iid)
        parent = self.tree.item(parent_iid)

        if not selected_iid:  # No item selected
            tkinter.messagebox.showerror("Error", "No item selected.")
            raise BitmexGUIException("No item selected.")

        name = parent["text"]
        symbol = selected["text"]

        return name, symbol

    def show(self):
        """
        Overriding so that this window updates its positions when shown.
        """
        AbstractChild.show(self)
        self.update_instruments()

    def update_instruments(self):
        """
        Query backend for open instruments and place them into treeview.
        """
        self.tree.delete(*self.tree.get_children())
        accs = core.instrument_info([x["name"] for x in accounts.get_all()])

        # Fill tree
        for account in accs:
            name = account["name"]
            instruments = account["instruments"]
            instruments.sort(key=lambda x: x["symbol"], reverse=False)  # Sort

            parent = self.tree.insert("", "end", text=name, open=True,
                                      values=["" for x in self.VAR])

            for instrument in instruments:
                values = []
                for v in self.VAR:
                    values.append(str(instrument[v]))

                self.tree.insert(parent, "end", text=instrument["symbol"],
                                 values=values)
                #self.tree.insert("", "end", text=position["symbol"],
                #                 values=values)

        # Resize tree
        new_height = len(self.tree.get_children()) * self.TREE_HEIGHT_MULTIPLIER
        if new_height < self.MIN_TREE_HEIGHT:
            new_height = self.MIN_TREE_HEIGHT
        if new_height > self.MAX_TREE_HEIGHT:
            new_height = self.MAX_TREE_HEIGHT
        self.tree.configure(height=new_height)
        self.tree.pack()

    def set_leverage(self):
        """
        Query backend to set new leverage.
        """
        name, symbol = self._get_selected()
        leverage = int(self.levSpin.get())
        try:
            core.position_leverage([name], symbol, leverage)
            self.update_instruments()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def set_risk_limit(self):
        """
        Query backend to set new risk limit.
        """
        name, symbol = self._get_selected()
        riskLimit = int(self.riskSpin.get())
        try:
            core.position_risk_limit([name], symbol, riskLimit)
            self.update_instruments()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))


class ActiveOrders(AbstractChild):
    """
    Window for listing all active orders per each account. Is able to set their
    limit price and contract quantity.
    """

    TITLE = "Active Orders"
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    TREE_HEIGHT_MULTIPLIER = 3
    COLUMN_PARAMS = {
        "width": 100
    }
    VAR = (
        "qty",
        "orderPrice",
        "displayQty",
        "filled",
        "remaining",
        "orderValue",
        "fillPrice",
        "type",
        "status",
        "execInst",
        "time"
    )
    FIRST_TEXT = "Symbol"
    TEXT = (
        "Qty",
        "Order Price",
        "Display Qty",
        "Filled",
        "Remaining",
        "Order Value",
        "Fill Price",
        "Type",
        "Status",
        "execInst",
        "Time"
    )
    FIRST_WIDTH = 100
    WIDTH = (
        40,
        100,
        90,
        60,
        90,
        100,
        100,
        50,
        60,
        200,
        190
    )

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(frame)
        updateButton = tkinter.Button(subframe,
                                      text="Update",
                                      command=self.update_orders)
        cancelButton = tkinter.Button(subframe,
                                      text="Cancel Order",
                                      command=self.cancel_order)
        self.qtySpin = tkinter.Spinbox(subframe, from_=1, to=SPINBOX_LIMIT)
        qtyButton = tkinter.Button(subframe,
                                   text="Amend Quantity",
                                   command=self.amend_quantity)
        self.pxSpin = tkinter.Spinbox(subframe, from_=1, to=SPINBOX_LIMIT)
        pxButton = tkinter.Button(subframe,
                                  text="Amend Order Price",
                                  command=self.amend_limit_price)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text=self.FIRST_TEXT, anchor=tkinter.W)
        self.tree.column("#0", width=self.FIRST_WIDTH)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        updateButton.grid(column=0, row=0)
        cancelButton.grid(column=1, row=0)
        self.qtySpin.grid(column=0, row=1)
        qtyButton.grid(column=1, row=1)
        self.pxSpin.grid(column=0, row=2)
        pxButton.grid(column=1, row=2)
        self.tree.pack()
        subframe.pack()
        frame.pack()

    def _get_selected(self):
        """
        Returns tupple of currently selected (account name, order id).
        """
        selected_iid = self.tree.focus()
        parent_iid = self.tree.parent(selected_iid)
        parent = self.tree.item(parent_iid)

        if not selected_iid:  # No item selected
            tkinter.messagebox.showerror("Error", "No item selected.")
            raise BitmexGUIException("No item selected.")

        name = parent["text"]
        id = selected_iid

        return name, id

    def show(self):
        """
        Overriding so that this window updates its positions when shown.
        """
        AbstractChild.show(self)
        self.update_orders()

    def update_orders(self):
        """
        Query backend for active orders and place them into treeview.
        """
        self.tree.delete(*self.tree.get_children())
        accs = core.active_order_info([x["name"] for x in accounts.get_all()])

        # Fill tree
        for account in accs:
            name = account["name"]
            orders = account["orders"]
            orders.sort(key=lambda x: x["time"], reverse=True)  # Sort orders

            parent = self.tree.insert("", "end", text=name, open=True,
                                      values=["" for x in self.VAR])

            for order in orders:
                values = []
                for v in self.VAR:
                    values.append(str(order[v]))

                self.tree.insert(parent, "end", iid=order["orderID"],
                                 text=order["symbol"], values=values)
                #self.tree.insert("", "end", text=position["symbol"],
                #                 values=values)

        # Resize tree
        new_height = len(self.tree.get_children()) * self.TREE_HEIGHT_MULTIPLIER
        if new_height < self.MIN_TREE_HEIGHT:
            new_height = self.MIN_TREE_HEIGHT
        if new_height > self.MAX_TREE_HEIGHT:
            new_height = self.MAX_TREE_HEIGHT
        self.tree.configure(height=new_height)
        self.tree.pack()

    def cancel_order(self):
        """
        Query backend to cancel order.
        """
        name, id = self._get_selected()
        try:
            core.order_cancel(name, id)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def amend_quantity(self):
        """
        Query backend to set new order quantity.
        """
        name, id = self._get_selected()
        qty = int(self.qtySpin.get())
        try:
            core.order_qty(name, id, qty)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def amend_limit_price(self):
        """
        Query backend to set new limit price.
        """
        name, id = self._get_selected()
        price = int(self.pxSpin.get())
        try:
            core.order_price(name, id, price)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))


class StopOrders(AbstractChild):
    """
    Window for listing all stop and take profit orders per each account. Is able
    to set their limit price, stop price and contract quantity.
    """

    TITLE = "Stop Orders"
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    TREE_HEIGHT_MULTIPLIER = 3
    COLUMN_PARAMS = {
        "width": 100
    }
    VAR = (
        "qty",
        "orderPrice",
        "filled",
        "stopPrice",
        "fillPrice",
        "type",
        "status",
        "execInst",
        "time"
    )
    FIRST_TEXT = "Symbol"
    TEXT = (
        "Qty",
        "Order Price",
        "Filled",
        "Stop Price",
        "Fill Price",
        "Type",
        "Status",
        "execInst",
        "Time"
    )
    FIRST_WIDTH = 100
    WIDTH = (
        40,
        100,
        60,
        100,
        100,
        120,
        70,
        200,
        200,
    )

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame, height=self.MIN_TREE_HEIGHT)
        subframe = tkinter.Frame(frame)
        updateButton = tkinter.Button(subframe,
                                      text="Update",
                                      command=self.update_orders)
        cancelButton = tkinter.Button(subframe,
                                      text="Cancel Order",
                                      command=self.cancel_order)
        self.qtySpin = tkinter.Spinbox(subframe, from_=1, to=SPINBOX_LIMIT)
        qtyButton = tkinter.Button(subframe,
                                   text="Amend Quantity",
                                   command=self.amend_quantity)
        self.pxSpin = tkinter.Spinbox(subframe, from_=1, to=SPINBOX_LIMIT)
        pxButton = tkinter.Button(subframe,
                                  text="Amend Order Price",
                                  command=self.amend_limit_price)
        self.stopSpin = tkinter.Spinbox(subframe, from_=1, to=SPINBOX_LIMIT)
        stopButton = tkinter.Button(subframe,
                                    text="Amend Stop Price",
                                    command=self.amend_stop_price)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text=self.FIRST_TEXT, anchor=tkinter.W)
        self.tree.column("#0", width=self.FIRST_WIDTH)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        updateButton.grid(column=0, row=0)
        cancelButton.grid(column=1, row=0)
        self.qtySpin.grid(column=0, row=1)
        qtyButton.grid(column=1, row=1)
        self.pxSpin.grid(column=0, row=2)
        pxButton.grid(column=1, row=2)
        self.stopSpin.grid(column=0, row=3)
        stopButton.grid(column=1, row=3)
        self.tree.pack()
        subframe.pack()
        frame.pack()

    def _get_selected(self):
        """
        Returns tupple of currently selected (account name, order id).
        """
        selected_iid = self.tree.focus()
        parent_iid = self.tree.parent(selected_iid)
        parent = self.tree.item(parent_iid)

        if not selected_iid:  # No item selected
            tkinter.messagebox.showerror("Error", "No item selected.")
            raise BitmexGUIException("No item selected.")

        name = parent["text"]
        id = selected_iid

        return name, id

    def show(self):
        """
        Overriding so that this window updates its positions when shown.
        """
        AbstractChild.show(self)
        self.update_orders()

    def update_orders(self):
        """
        Query backend for stop orders and place them into treeview.
        """
        self.tree.delete(*self.tree.get_children())
        accs = core.stop_order_info([x["name"] for x in accounts.get_all()])

        # Fill tree
        for account in accs:
            name = account["name"]
            orders = account["orders"]
            orders.sort(key=lambda x: x["time"], reverse=True)  # Sort orders

            parent = self.tree.insert("", "end", text=name, open=True,
                                      values=["" for x in self.VAR])

            for order in orders:
                values = []
                for v in self.VAR:
                    values.append(str(order[v]))

                self.tree.insert(parent, "end", iid=order["orderID"],
                                 text=order["symbol"], values=values)
                #self.tree.insert("", "end", text=position["symbol"],
                #                 values=values)

        # Resize tree
        new_height = len(self.tree.get_children()) * self.TREE_HEIGHT_MULTIPLIER
        if new_height < self.MIN_TREE_HEIGHT:
            new_height = self.MIN_TREE_HEIGHT
        if new_height > self.MAX_TREE_HEIGHT:
            new_height = self.MAX_TREE_HEIGHT
        self.tree.configure(height=new_height)
        self.tree.pack()

    def cancel_order(self):
        """
        Query backend to cancel order.
        """
        name, id = self._get_selected()
        try:
            core.order_cancel(name, id)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def amend_quantity(self):
        """
        Query backend to set new order quantity.
        """
        name, id = self._get_selected()
        qty = int(self.qtySpin.get())
        try:
            core.order_qty(name, id, qty)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def amend_limit_price(self):
        """
        Query backend to set new limit price.
        """
        name, id = self._get_selected()
        price = int(self.pxSpin.get())
        try:
            core.order_price(name, id, price)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def amend_stop_price(self):
        """
        Query backend to set new stop price.
        """
        name, id = self._get_selected()
        stop = int(self.stopSpin.get())
        try:
            core.order_stop_price(name, id, stop)
            self.update_orders()
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))


class OrderHistory(AbstractChild):
    """
    Window for listing all orders for each account, even closed ones.
    """

    TITLE = "Order History"
    MIN_TREE_HEIGHT = 10
    MAX_TREE_HEIGHT = 30
    TREE_HEIGHT_MULTIPLIER = 5
    COLUMN_PARAMS = {
        "width": 100
    }
    VAR = (
        "symbol",
        "qty",
        "orderPrice",
        "displayQty",
        "filled",
        "stopPrice",
        "fillPrice",
        "type",
        "status",
        "execInst",
        "time"
    )
    TEXT = (
        "Symbol",
        "Qty",
        "Order Price",
        "Display Qty",
        "Filled",
        "Stop Price",
        "Fill Price",
        "Type",
        "Status",
        "execInst",
        "Time"
    )
    WIDTH = (
        70,
        40,
        100,
        70,
        60,
        100,
        100,
        120,
        70,
        200,
        200,
    )

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        frame = tkinter.Frame(self)
        self.tree = tkinter.ttk.Treeview(frame, height=self.MIN_TREE_HEIGHT)
        button = tkinter.Button(frame,
                                text="Update",
                                command=self.update_orders)

        self.tree["columns"] = self.VAR
        self.tree.heading("#0", text="Order ID", anchor=tkinter.W)
        self.tree.column("#0", width=320)
        for v, t, w in zip(self.VAR, self.TEXT, self.WIDTH):
            self.tree.heading(v, text=t, anchor=tkinter.W)
            self.tree.column(v, width=w)

        self.tree.pack()
        button.pack()
        frame.pack()

    def show(self):
        """
        Overriding so that this window updates its positions when shown.
        """
        AbstractChild.show(self)
        self.update_orders()

    def update_orders(self):
        """
        Query backend for order history and place it into treeview.
        """
        self.tree.delete(*self.tree.get_children())
        accs = core.history_order_info([x["name"] for x in accounts.get_all()])

        # Fill tree
        for account in accs:
            name = account["name"]
            orders = account["orders"]
            orders.sort(key=lambda x: x["time"], reverse=True)  # Sort orders
            parent = self.tree.insert("", "end", text=name, open=True,
                                      values=["" for x in self.VAR])

            for order in orders:
                values = []
                for v in self.VAR:
                    values.append(str(order[v]))

                self.tree.insert(parent, "end", text=order["orderID"],
                                 values=values)
                #self.tree.insert("", "end", text=position["symbol"],
                #                 values=values)

        # Resize tree
        new_height = len(self.tree.get_children()) * self.TREE_HEIGHT_MULTIPLIER
        if new_height < self.MIN_TREE_HEIGHT:
            new_height = self.MIN_TREE_HEIGHT
        if new_height > self.MAX_TREE_HEIGHT:
            new_height = self.MAX_TREE_HEIGHT
        self.tree.configure(height=new_height)
        self.tree.pack()


class Calculator(AbstractChild):
    """
    Window for calculating theoretical PNL.
    """

    TITLE = "PNL Calculator"
    SIGNIFICANT_FIGURES = 5

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        # Backend
        try:
            openInstruments = core.open_instruments(accounts.get_all()[0]["name"])
            openInstruments.sort()
        except IndexError:
            print("Warning: No accounts were created yet.")
            openInstruments = []
        except Exception as e:
            print(e)
            openInstruments = []

        # Frontend
        mainFrame = tkinter.Frame(self)
        upperFrame = tkinter.Frame(mainFrame)
        lowerFrame = tkinter.Frame(mainFrame)
        buttonFrame = tkinter.Frame(mainFrame)

        self.symVar = tkinter.StringVar(self)

        symLabel = tkinter.Label(upperFrame, text="Symbol:")
        symCombo = tkinter.ttk.Combobox(upperFrame, textvariable=self.symVar)
        symCombo["values"] = openInstruments
        qtyLabel = tkinter.Label(upperFrame, text="Quantity:")
        self.qtySpin = tkinter.Spinbox(upperFrame, from_=1, to=SPINBOX_LIMIT)
        entLabel = tkinter.Label(upperFrame, text="Entry Price:")
        self.entSpin = tkinter.Spinbox(upperFrame, from_=1, to=SPINBOX_LIMIT)
        extLabel = tkinter.Label(upperFrame, text="Exit Price:")
        self.extSpin = tkinter.Spinbox(upperFrame, from_=1, to=SPINBOX_LIMIT)
        levLabel = tkinter.Label(upperFrame, text="Leverage:")
        self.levSpin = tkinter.Spinbox(upperFrame, from_=1, to=SPINBOX_LIMIT)

        enVLabel = tkinter.Label(lowerFrame, text="Entry Value:")
        self.enVLabel = tkinter.Label(lowerFrame)
        exVLabel = tkinter.Label(lowerFrame, text="Exit Value:")
        self.exVLabel = tkinter.Label(lowerFrame)
        pnlLabel = tkinter.Label(lowerFrame, text="Profit/Loss:")
        self.pnlLabel = tkinter.Label(lowerFrame)
        perLabel = tkinter.Label(lowerFrame, text="Profit/Loss %:")
        self.perLabel = tkinter.Label(lowerFrame)
        roeLabel = tkinter.Label(lowerFrame, text="ROE %:")
        self.roeLabel = tkinter.Label(lowerFrame)

        longButton = tkinter.Button(buttonFrame, text="Calculate Long",
                                    command=lambda: self.calculate(short=False))
        shortButton = tkinter.Button(buttonFrame, text="Calculate Short",
                                     command=lambda: self.calculate(short=True))

        symLabel.grid(column=0, row=0)
        symCombo.grid(column=1, row=0)
        qtyLabel.grid(column=0, row=1)
        self.qtySpin.grid(column=1, row=1)
        entLabel.grid(column=0, row=2)
        self.entSpin.grid(column=1, row=2)
        extLabel.grid(column=0, row=3)
        self.extSpin.grid(column=1, row=3)
        levLabel.grid(column=0, row=4)
        self.levSpin.grid(column=1, row=4)

        enVLabel.grid(column=0, row=0)
        self.enVLabel.grid(column=1, row=0)
        exVLabel.grid(column=0, row=1)
        self.exVLabel.grid(column=1, row=1)
        pnlLabel.grid(column=0, row=2)
        self.pnlLabel.grid(column=1, row=2)
        perLabel.grid(column=0, row=3)
        self.perLabel.grid(column=1, row=3)
        roeLabel.grid(column=0, row=4)
        self.roeLabel.grid(column=1, row=4)

        longButton.grid(column=0, row=0)
        shortButton.grid(column=1, row=0)

        upperFrame.pack()
        lowerFrame.pack()
        buttonFrame.pack()
        mainFrame.pack()

    def calculate(self, short=False):
        """
        Get values from spinboxes, calculate and update labels.
        """
        # Get values
        symbol = self.symVar.get()
        qty = float(self.qtySpin.get())
        entryPx = float(self.entSpin.get())
        exitPx = float(self.extSpin.get())
        leverage = float(self.levSpin.get())

        if symbol == "":
            tkinter.messagebox.showerror("Error", "Symbol is required.")

        # Calculation
        try:
            foo = accounts.get_all()[0]["name"]
            inverse = core.instrument_is_inverse(foo, symbol)
            entryValue = core.instrument_margin_per_contract(foo, symbol, entryPx)
            exitValue = core.instrument_margin_per_contract(foo, symbol, exitPx)
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))
            raise e
        entryValue *= qty
        exitValue *= qty

        if short != inverse:
            # Short or long + inverse
            pnl = entryValue - exitValue
        else:
            # Long or short + inverse
            pnl = exitValue - entryValue
        percent = pnl / entryValue * 100
        percent = significant_figures(percent, self.SIGNIFICANT_FIGURES)

        roe = pnl / entryValue * leverage * 100
        roe = significant_figures(roe, self.SIGNIFICANT_FIGURES)

        # Set values
        self.enVLabel.configure(text=str(entryValue))
        self.exVLabel.configure(text=str(exitValue))
        self.pnlLabel.configure(text=str(pnl))
        self.perLabel.configure(text=str(percent))
        self.roeLabel.configure(text=str(roe))
