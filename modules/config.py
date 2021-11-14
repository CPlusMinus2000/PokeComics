# File for constants, hence "configuration"

import discord

from typing import List, Dict, Union, Any
from datetime import datetime
from words.words import words

Member = Dict[str, Union[str, int, Dict[str, List[bool]]]]

# NUM_DIGITS is a really important constant -- it governs how much padding
# the program looks for in comic numbers. The fact that my comics
# are numbered with a zfill of 3 is accounted for by NUM_DIGITS, and
# if I ever hit a higher counter, this will have to be changed. Yes, there
# are other ways to do this, but this is for historical reasons.
# Hopefully this never breaks.
NUM_DIGITS = 3

POINTS_DEFAULT = 100
SADPIP_ID = 825045713515315261
WORDS_DEFAULT_LENGTH = 5
RPHONE_DEFAULT_LENGTH = 3
RPHONE_TOPICS = {
    "main": "",
    "world": 'w',
    "battle": 'b',
    "people": 'p',
    "scitech": 's',
    "other": 'o'
}

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


def default_member(mem: discord.Member) -> Member:
    """
    Makes a default member. This has to get updated every time
    the schema changes to adapt to whatever weird change Colin makes.
    """

    return {
        "name": mem.name,
        "daily": datetime.min.isoformat(),
        "streak": 0,
        "points": POINTS_DEFAULT,  # Default value for points
        "pity": 0,  # Pity timer for the slots
        "facts": {  # Initialize the seen list for all facts
            w: [False] * WORDS_DEFAULT_LENGTH for w in words
        },
        "rphone": {
            t: [False] * RPHONE_DEFAULT_LENGTH
            for t in RPHONE_TOPICS if t != "main"
        },
    }
