"""
Internally managing accounts.
"""

from json import dumps, loads

from backend.exceptions import BitmexAccountsException


# Constants

HOST = "https://www.bitmex.com/"  # Default host for new accounts
SAVEFILE = "./accounts"  # Default account savefile location


# Accounts list

_accounts = []  # Stores all loaded accounts


# Methods

def new(name: str, key: str, secret: str, host: str = HOST):
    """
    Create new account dict.

    name:   name of account for internal identification
    key:    api key
    secret: api secret
    host:   url of bitmex server for this account (https:// has to be included)

    Returns created account dict.
    """
    if name in [x["name"] for x in _accounts]:
        raise BitmexAccountsException("Account '" + name + "' already exists.")
    d = {
        "name": name,
        "key": key,
        "secret": secret,
        "host": host
    }
    _accounts.append(d)
    return d


def delete(name: str):
    """
    Delete account with matching name from loaded.

    name:   name of account to be deleted
    """
    for i, account in enumerate(_accounts):
        if account["name"] == name:
            _accounts.pop(i)


def get(name: str):
    """
    Get account by name.

    name:   name of account

    Returns account dict or None if account with name doesn't exist.
    """
    for account in _accounts:
        if account["name"] == name:
            return account

def get_all():
    """
    Returns all loaded accounts as list. Warning: Do NOT make any changes to
    returned list.
    """
    return _accounts


def save(savefile: str = SAVEFILE):
    """
    Save accounts as json list to file. Warning: Replaces old savefile.

    savefile:   location of savefile
    """
    try:
        f = open(savefile, "w")
    except Exception as e:
        raise BitmexAccountsException(str(e))

    f.write(dumps(_accounts))
    f.close()


def load(savefile: str = SAVEFILE):
    """
    Load accounts from a savefile. Warning: Replaces loaded accounts.

    savefile:   location of savefile
    """
    try:
        f = open(savefile, "r")
    except Exception as e:
        raise BitmexAccountsException("Internal Error: " + str(e) + "Does '" +
                                      savefile + "' really exist?")

    json = f.read()

    try:
        dict = loads(json)
    except Exception as e:
        raise BitmexAccountsException("Internal Error: " + str(e) + "Is '" +
                                      savefile + "' really an account savefile?")

    _accounts.clear()
    for account in dict:
        _accounts.append(account)
