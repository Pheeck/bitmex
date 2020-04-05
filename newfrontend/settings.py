"""
Settings window class and related classes.
"""

import tkinter

import newfrontend.settingsframes as frames

import backend.core as core
import backend.accounts as accounts

from backend.exceptions import BitmexAccountsException


#
# Constants
#

DESTROY_DELAY = 200  # Delay before window destroys itself at quit() method call



#
# Settings related classes
#

class AbstractChild(tkinter.Tk):
    """
    Abstract class. Only for inheriting.

    Super of all child windows. Can be hidden and remembers its geometry.

    Duplicate of frontend.AbstractChild so that code from newfrontend doesn't
    directly depend on code from (old) frontend.
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


#
# Settings class
#

class Settings(AbstractChild):
    """
    Window for viewing accounts, creating accounts, deleting accounts,
    configuring program and configuring bot.
    """

    TITLE = "BitMEX Settings"

    def __init__(self, *args, **kvargs):
        AbstractChild.__init__(self, *args, **kvargs)

        mainFrame = tkinter.Frame(self)
        self.accFrame = frames.AccountManagement(mainFrame, self)
        self.botFrame = frames.BotManagement(mainFrame)

        self.accFrame.pack()
        self.botFrame.pack()
        mainFrame.pack()

        self.login = None

    def update(self):
        """
        Overriding update method to also update login window.
        """
        if not self.login is None:
            if self.login.isAlive:
                self.login.update()
            else:  # Login window was just closed
                self.accFrame.update_accounts()
                self.login = None
        AbstractChild.update(self)

    def open_login(self):
        """
        Open login window.
        """
        if self.login is None:
            self.login = Login()

    def toggle_hidden(self):
        """
        Overriding toggle hidden function to also update values of this
        window's frames.
        """
        AbstractChild.toggle_hidden(self)
        self.accFrame.update_values()
        self.botFrame.update_values()
