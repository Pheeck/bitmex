"""
Frontend utility functions.
"""

from math import log10, floor


def significant_figures(x, figures):
    """
    Returns number rounded using significant figures.

    x:          number to be rounded
    figures:    how many figures should be left not rounded

    Returns rounded int or float.
    """
    if x == 0:
        return x
    return round(x, -int(floor(log10(abs(x)))) + figures - 1)


def sf_on_dict(d, figures):
    """
    Recursively applies significant_figures() on list/dict structure where
    the outer layer is dict.

    d:          dict to be used
    figures:    how many figures should be left not rounded

    In-place
    """
    for key in d.keys():
        item = d[key]
        if isinstance(item, dict):
            sf_on_dict(item, figures)
        elif isinstance(item, list):
            sf_on_list(item, figures)
        elif isinstance(item, int) or isinstance(item, float):
            d[key] = significant_figures(item, figures)


def sf_on_list(l, figures):
    """
    Recursively applies significant_figures() on list/dict structure where
    the outer layer is list.

    l:          list to be used
    figures:    how many figures should be left not rounded

    In-place
    """
    for i, item in enumerate(l):
        if isinstance(item, dict):
            sf_on_dict(item, figures)
        elif isinstance(item, list):
            sf_on_list(item, figures)
        elif isinstance(item, int) or isinstance(item, float):
            d[key] = significant_figures(item, figures)
