"""
Landing page window class.
"""

import tkinter

import newfrontend.landingframes as frames

from frontend.windows import Calculator
from newfrontend.settings import Settings

import backend.accounts as accounts
from backend.exceptions import BitmexAccountsException


#
# Constants
#


DESTROY_DELAY = 200  # Delay before window destroys itself at quit() method call


#
# Classes
#

class Landing(tkinter.Tk):
    """
    Landing page of program. Substitution for main window from old fronend.
    """

    TITLE = "BitMEX Assistant"

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
        calcWindow = Calculator(hidden=True)
        settWindow = Settings(hidden=True)

        self.windows = [
            calcWindow,
            settWindow,
        ]

        # Menu
        menu = tkinter.Menu()
        menu.add_command(label="PnL Calculator", command=lambda: calcWindow.toggle_hidden())
        menu.add_command(label="Settings", command=lambda: settWindow.toggle_hidden())
        self.configure(menu=menu)

        # Widgets
        mainFrame = tkinter.Frame(self)
        self.overFrame = frames.Overview(mainFrame)
        self.accFrame = frames.Accounts(mainFrame)
        self.posFrame = frames.Positions(mainFrame)
        self.orderFrame = frames.Order(mainFrame)

        self.overFrame.pack()
        self.accFrame.pack()
        self.posFrame.pack()
        self.orderFrame.pack()
        mainFrame.pack()

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
