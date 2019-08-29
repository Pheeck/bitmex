"""
Custom exceptions.
"""


class BitmexException(Exception):
    pass


class BitmexApiException(BitmexException):
    pass


class BitmexAccountsException(BitmexException):
    pass


class BitmexCoreException(BitmexException):
    pass


class BitmexCoreMultiException(BitmexCoreException):
    def __init__(self, *args):
        self.accounts = []
        self.exceptions = []
        self.tracebacks = []
        self.args = args

    def __str__(self):
        result = "Core Error:\n"
        for account, exception in zip(self.accounts, self.exceptions):
            result += account["name"] + ": " + str(exception) + "\n"
        if self.args:
            result += "args:\n"
            for arg in self.args:
                result += str(arg) + "\n"
        return result


class BitmexGUIException(BitmexException):
    pass
