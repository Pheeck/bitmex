"""
Frames for settings window.
"""

import tkinter
import tkinter.messagebox
import tkinter.ttk

import backend.core as core
import backend.accounts as accounts

from backend.exceptions import BitmexGUIException


#
# Classes
#

class AccountManagement(tkinter.Frame):
    """
    Frame for viewing, creating and deleting accounts.
    """

    def __init__(self, parent, window, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)

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

        self.update_accounts()

        newButton.grid(column=0, row=0)
        delButton.grid(column=1, row=0)
        self.tree.pack()
        subframe.pack()

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
        self.update_accounts()


class Bot(tkinter.Frame):

    def __init__(self, *args, **kvargs):
        tkinter.Frame.__init__(self, *args, **kvargs)
