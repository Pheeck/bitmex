"""
Frames for settings window.
"""

import tkinter
import tkinter.messagebox
import tkinter.ttk

import backend.core as core
import backend.accounts as accounts

from backend.exceptions import BitmexGUIException

import bot.settings


#
# Constants
#

SPINBOX_LIMIT = 1000000000
RETRY_DELAY = 9000  # Standard delay before trying to request crucial data again


#
# Classes
#

class AccountManagement(tkinter.Frame):
    """
    Frame for viewing, creating and deleting accounts.
    """

    TITLE = "Accounts management"

    def __init__(self, parent, window, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, parent, *args, text=self.TITLE, **kwargs)

        self.window = window

        self.tree = tkinter.ttk.Treeview(self)
        subframe = tkinter.Frame(self)
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

        newButton.grid(column=0, row=0)
        delButton.grid(column=1, row=0)
        self.tree.pack()
        subframe.pack()

    def update_values(self):
        """
        Query backend for loaded accounts and place them into treeview.

        Usually called by settings window when opened.
        """
        self.tree.delete(*self.tree.get_children())
        for account in accounts.get_all():
            self.tree.insert("", "end", text=account["name"],
                             values=(account["host"], account["key"]))

    def new_account(self):
        """
        Prepare to add new account.
        """
        self.window.open_login()

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
        self.update_values()


class BotManagement(tkinter.Frame):
    """
    Frame for configuring bot.
    """

    TITLE = "Bot settings"

    PRIORITY_SYMBOLS = (
        "XBTUSD",
        "ETHUSD"
    )
    DEFAULT_TRADE_PX = 1000
    DEFAULT_CLOSE_PX = 100

    def __init__(self, *args, **kwargs):
        tkinter.LabelFrame.__init__(self, *args, text=self.TITLE, **kwargs)

        # Frontend
        self.firstVar = tkinter.StringVar(self)
        self.secondVar = tkinter.StringVar(self)

        firstLabel = tkinter.Label(self, text="First contract symbol:")
        secondLabel = tkinter.Label(self, text="Second contract symbol:")
        tradeLabel = tkinter.Label(self, text="Trade if difference this high:")
        closeLabel = tkinter.Label(self, text="Close if difference this low:")


        self.firstCombo = tkinter.ttk.Combobox(self, textvariable=self.firstVar)
        self.secondCombo = tkinter.ttk.Combobox(self, textvariable=self.secondVar)
        self.tradeSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT)
        self.closeSpin = tkinter.Spinbox(self, from_=1, to=SPINBOX_LIMIT)

        self.tradeSpin.delete(0)
        self.tradeSpin.insert(0, self.DEFAULT_TRADE_PX)
        self.closeSpin.delete(0)
        self.closeSpin.insert(0, self.DEFAULT_CLOSE_PX)

        saveButton = tkinter.Button(self, text="Save bot settings",
                                    command=self.save_settings)

        # Backend
        self._fetch_instruments()

        # Frontend again
        firstLabel.grid(column=0, row=0)
        self.firstCombo.grid(column=1, row=0)
        secondLabel.grid(column=0, row=1)
        self.secondCombo.grid(column=1, row=1)
        tradeLabel.grid(column=0, row=2)
        self.tradeSpin.grid(column=1, row=2)
        closeLabel.grid(column=0, row=3)
        self.closeSpin.grid(column=1, row=3)
        saveButton.grid(column=1, row=4)

    def update_values(self):
        """
        Query bot backend for current settings and update this frame in
        accordance.

        Usually called by settings window when opened.
        """
        self.firstVar.set(bot.settings.get_first_contract())
        self.secondVar.set(bot.settings.get_second_contract())
        self.tradeSpin.delete(0, len(self.tradeSpin.get()))
        self.tradeSpin.insert(0, bot.settings.get_trade_difference())
        self.closeSpin.delete(0, len(self.tradeSpin.get()))
        self.closeSpin.insert(0, bot.settings.get_close_difference())

    def save_settings(self):
        """
        Updates bot settings values in bot backend in accordance to current
        state of this frame's inputs.
        """
        bot.settings.set_first_contract(self.firstVar.get())
        bot.settings.set_second_contract(self.secondVar.get())
        bot.settings.set_trade_difference(int(self.tradeSpin.get()))
        bot.settings.set_close_difference(int(self.closeSpin.get()))
        self.update_values()

    def _fetch_instruments(self):
        """
        Request list of open instruments from api.
        Then populate this frame's symbol comboboxes with it.

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
        self.firstVar.set(openInstruments[0])
        self.secondVar.set(openInstruments[0])

        # Populate comboboxes
        self.firstCombo["values"] = openInstruments
        self.secondCombo["values"] = openInstruments
