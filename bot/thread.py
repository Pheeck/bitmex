"""
Functions used to run, stop and manage bot thread.
"""

import threading

import bot.bot as bot


# Functions

def run_bot(*args, **kvargs):
    """
    Create new thread and run main bot function on it.
    args and kvargs of this function are passed to bot main function.

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
    pass
