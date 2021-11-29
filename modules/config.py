# File for constants, hence "configuration"

import discord
import os
import subprocess as sp

from dotenv import load_dotenv
from typing import List, Dict, Tuple, Union, Optional
from datetime import datetime, date, time
from words.words import words
from os.path import getmtime
from time import sleep

Member = Dict[str, Union[str, int, Dict[str, List[bool]]]]
Comic = Dict[str, Union[str, int, bool]]

# Some Discord authentication information
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

# NUM_DIGITS is a really important constant -- it governs how much padding
# the program looks for in comic numbers. The fact that my comics
# are numbered with a zfill of 3 is accounted for by NUM_DIGITS, and
# if I ever hit a higher counter, this will have to be changed. Yes, there
# are other ways to do this, but this is for historical reasons.
# Hopefully this never breaks.
NUM_DIGITS = 3

# Some common database search filters
MEMBERS = {"name": "members"}
VIEWSTATS = {"name": "viewstats"}

# Do I need to make her get up early?
BOUNDS = False
TIMEZONE = 3
STIME = time(5 + TIMEZONE, 0, 0) if BOUNDS else time(0, 0, 0)
WDETIME = time(8 + TIMEZONE, 10, 10, 10010) if BOUNDS else time.max
WEETIME = time(8 + TIMEZONE, 10, 10, 10010) if BOUNDS else time.max

# File conversion stuff
CONVERT = 'convert "%s" "%s" 2> /dev/null'
IMAGE_WIDTH = 1200
CONVERTR = f'convert "%s" -resize {IMAGE_WIDTH} "%s" 2> /dev/null'

POINTS_DEFAULT = 100
SADPIP_ID = 825045713515315261
SADPIP_STR = f"<:sadpip:{SADPIP_ID}>"
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

# Turns out these are quite useful, so let's make them constants
RPHONE_TOPICS_PAID = {t for t in RPHONE_TOPICS if t != "main"}
RPHONE_HEADERS = {f"r{h}" for h in RPHONE_TOPICS.values()}
PURCHASE_FIELDS = {
    "facts": sorted(words.keys()),
    "rphone": sorted(
        RPHONE_TOPICS_PAID,
        key=lambda t: "zzzzz" if t.lower() == "other" else t
    )
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

# Slots, names and payouts
SLOT_INFO = {
    "berries": 2,
    "lightning": 10,
    "moon": 15,
    "replay": 15,
    "7": 300,
    "galactic": 100
}

SLOT_FAIL = "FAIL"
SLOTS_PRICE = 2


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

    return STIME, WEETIME if day in [5, 6] else WDETIME


def create_png(
    tif: str, 
    dest: Optional[str]=None,
    resize: bool=False
) -> str:
    """
    Creates a png from a tif.
    TODO: Look into os.chmod, and also not using asyncio.sleep
    """

    if tif.count(".tif") > 1:
        raise ValueError("Multiple .tifs found in filename")
    
    new = dest if dest is not None else tif.replace(".tif", ".png")
    convert = CONVERT % (tif, new) if not resize else CONVERTR % (tif, new)
    if not os.path.exists(new) or getmtime(tif) > getmtime(new):
        print(f"Converting {tif} to {new}")
        sp.run(convert.split()) 
        sp.run(f"chmod a+rx {new}".split())
    
    return new
