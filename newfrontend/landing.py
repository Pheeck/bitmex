"""
Landing page window class.
"""

import tkinter
import sys

import tkinter.messagebox

import newfrontend.landingframes as frames

from frontend.windows import Calculator
from newfrontend.settings import Settings

import backend.accounts as accounts
from backend.exceptions import BitmexAccountsException, BitmexBotException

import bot.log
import bot.settings


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

    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        # Backend
        try:
            accounts.load()
        except BitmexAccountsException:
            print("No accounts savefile found, creating a blank one now...")
            accounts.save()
            accounts.load()

        # Bot
        try:
            bot.log.read_entries(1)
        except BitmexBotException:
            print("No bot log savefile found")
            do_reset = tkinter.messagebox.askyesno("Reset bot log file", "No " +
                                                   "valid bot log file found. "+
                                                   "Do you want to create a " +
                                                   "new one?\n" + "Warning: " +
                                                   "This will reset the old " +
                                                   "log if it exists.")
            if do_reset:
                bot.log.reset()
            else:
                sys.exit()

        try:
            bot.settings.load()
        except BitmexBotException:
            print("No bot settings savefile found, creating a blank one now...")
            bot.settings.save()
            bot.settings.load()

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
        self.botFrame = frames.Bot(mainFrame)

        self.overFrame.pack(fill=tkinter.X)
        self.accFrame.pack()
        self.posFrame.pack(fill=tkinter.X)
        self.orderFrame.pack(fill=tkinter.X)
        self.botFrame.pack(fill=tkinter.X)
        mainFrame.pack()

        # Alive flag
        self.isAlive = True

    def update(self, *args, **kwargs):
        """
        Overriding update method to also update child windows.
        """
        for window in self.windows:
            window.update()
        tkinter.Tk.update(self, *args, **kwargs)

    def quit(self):
        """
        Cleans up and kills the program.
        """
        accounts.save()
        bot.settings.save()

        # Stop bot
        if self.botFrame.is_running():
            print("Bot still running. Halting it now...")
            self.botFrame.toggle_running()

        self.isAlive = False
        self.after(DESTROY_DELAY, self.destroy)
