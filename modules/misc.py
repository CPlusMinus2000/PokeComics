"""Miscellaneous helper functions for processing information"""
from typing import Tuple, List
from datetime import date, time
from glob import glob

import discord

# Colours
COLOURS = {
    "black": discord.Color.from_rgb(0, 0, 0),
    "blue": discord.Color.blue(),
    "brown": discord.Color.from_rgb(165, 42, 42),
    "gray": discord.Color.light_gray(),
    "green": discord.Color.green(),
    "pink": discord.Color.from_rgb(255, 192, 203),
    "purple": discord.Color.purple(),
    "red": discord.Color.red(),
    "white": discord.Color.from_rgb(255, 255, 255),
    "yellow": discord.Color.gold()
}


# Start and ending times (so morning comics can only be seen from 6:00-7:30)
#  but converted to E[SD]T because that's where I'm hosting the bot from
def bounds(day: int = date.today().weekday()) -> Tuple[time, time]:
    """Get the left/right bounds of when comics are available.
    
    Parameters
    ----------
    day : int
        A number (0-6) representing a day of the week.
        By default, it is the current day.
    """

    stime = time(8, 0, 0)
    etime = time(11, 10, 10, 10010) if day < 5 else time(11, 10, 10, 10010)
    
    return stime, etime

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

