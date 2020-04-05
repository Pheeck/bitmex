"""
Functions used to run, stop and manage bot thread.
"""

import threading

from time import sleep

import bot.bot as bot


# Functions

def run_bot(*args, **kwargs):
    """
    Create new thread and run main bot function on it.
    args and kwargs of this function are passed to bot main function.

    Returns created thread object.
    """
    thread = threading.Thread(
        target=bot.main,
        args=args,
        kwargs=kwargs,
    )
    thread.start()
    return thread

def stop_bot(thread):
    """
    Halts bot thread given as argument.
    """
    bot.set_kill_flag_true()
    thread.join()
