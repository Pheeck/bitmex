"""
Landing page window class.
"""

import tkinter

import newfrontend.frames as frames

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
        # TODO
        self.windows = []

        # Widgets
        mainFrame = tkinter.Frame(self)
        self.menuFrame = frames.Menu(mainFrame)
        self.overFrame = frames.Overview(mainFrame)
        self.accFrame = frames.Accounts(mainFrame)
        self.posFrame = frames.Positions(mainFrame)
        self.orderFrame = frames.Order(mainFrame)

        self.menuFrame.pack()
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
