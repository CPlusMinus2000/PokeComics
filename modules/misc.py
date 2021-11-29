"""Miscellaneous helper functions for processing information"""
from typing import List
from glob import glob


def insensitive_glob(pattern) -> List[str]:
    """
    Does a case-insensitive globbing search.
    """

    def either(c):
        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
    
    return glob(''.join(map(either, pattern)))


def leading_num(s: str, stop: int = -1) -> int:
    """
    Tries to find as many digit characters at the start of s as possible,
    returning results as an integer, stopping at `stop` if stop >= 0.

    If there are no such digits, the function throws an error.
    """

    i = 1
    while s[:i].isdigit() and i <= len(s) and (stop < 0 or i < stop):
        i += 1
    
    return int(s[:(i - 1)])


def not_everyone(msg: str) -> bool:
    """
    Returns true if the message does not mention multiple people.
    """

    return "@everyone" not in msg and "@here" not in msg
