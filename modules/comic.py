"""All the functions for processing comics"""

import os
import discord
import asyncio

from typing import Union
from glob import glob
from pathlib import Path
from datetime import date, datetime

from modules.database import db_update, get_date, get_metadata, people
from modules.misc import bounds
from modules.config import NUM_DIGITS as ND, create_png

# Place where I store all the comics
SITE = "https://student.cs.uwaterloo.ca/~cqhe/"

# Emojis for reactions
LEFT = '◀️'
RIGHT = '▶️'
PIPLUP_ID = 824140724224000020
DELETE = '🗑️'

# File extensions that Discord can display directly
DISPLAY = (".png", ".PNG", ".jpg", ".jpeg", ".JPG", ".JPEG")

# List of authorized people
authorized = ["The20thIcosahedron"]

# List of readers
readers = ["claudineyip"]

def valid_comic(pathname: str, lviewed: int = 0) -> int:
    """
    Checks if a pathname represents a valid comic, i.e.
    satisfies the naming conventions and is below lviewed
    (if lviewed is greater than 0).

    Returns the comic's number if the name is valid, and -1 otherwise.
    """

    parts = pathname.split('/')
    if len(parts) > 1 and parts[1][:ND].isdigit() and lviewed <= 0:
        return int(parts[1][:ND])
    elif len(parts) > 1 and parts[1][:ND].isdigit():
        cnum = int(parts[1][:ND])
        return cnum if cnum <= lviewed else -1
    else:
        return -1


def fetch_comic(cnum: int, coloured: bool = True) -> str:
    """
    Gets the comic with number 'cnum' if one exists.
    If a coloured version exists, it will be selected.
    """

    clink = glob(f"Comics/{str(cnum).zfill(ND)}*Colour*")
    if clink and coloured: # Not empty
        return clink[0]
    
    clink = glob(f"Comics/{str(cnum).zfill(ND)}*")
    if clink: # Not empty
        return clink[0]
    
    # This should hopefully never be reached
    return "ERROR"


async def send_comic(ctx, comic: Union[str, int], colour: bool = True):
    """
    Sends a comic, and also checks for possible necessary preparations.
    """

    if isinstance(comic, int):
        comic = fetch_comic(comic, colour)
    
    name = f"{Path.home()}/public_html/{os.path.splitext(comic)[0]}.png"
    await create_png(comic, dest=name)

    #TODO: Replace 4 with an actual not-hardcoded index
    fname = '/'.join(name.split('/')[4:]).replace(' ', "%20")
    msg = await ctx.send(f"{SITE}{fname}")
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
    await msg.add_reaction(emoji=f":pip:{PIPLUP_ID}")
    await msg.add_reaction(DELETE)


async def edit_comic(msg: discord.Message, comic: Union[str, int]):
    """
    Edits the message link in 'msg' with the comic.
    """

    if isinstance(comic, int):
        comic = fetch_comic(comic)

    target = f"{str(Path.home())}/public_html/"
    if not target.endswith(DISPLAY): # Convert to a displayable type
        target += f"{os.path.splitext(comic)[0]}.png"
        if not os.path.exists(target):
            os.system(f'convert "{comic}" "{target}" > /dev/null')
            os.system(f"chmod a+rx '{target}'")
    
    else: # Just copy it over, and maybe change permissions
        target += comic
        if not os.path.exists(target):
            os.system(f'cp "{comic}" "{target}"')
            os.system(f"chmod a+rx '{target}'")

    #TODO: Replace 4 with an actual not-hardcoded index
    fname = SITE + '/'.join(target.split('/')[4:]).replace(' ', "%20")
    await msg.edit(content=fname)


async def process_reaction_comic(reaction, user) -> None:
    """
    Processes a comic reaction.

    Parameters:
    -----------
    reaction : discord.Reaction
        The reaction object detected.
    user : discord.User
        The user who sent the reaction.
    """
    
    cont = reaction.message.content
    if reaction.emoji in [LEFT, RIGHT]: 
        # Comic message
        comic = cont.split('/')[-1]
        cnum = int(comic[:ND])
        lviewed = get_metadata("lviewed")
        latest = get_metadata("latest")
        update = get_date("updated")
        stime, etime = bounds()

        if reaction.emoji == LEFT and cnum > 1:
            await edit_comic(reaction.message, cnum - 1)
        
        elif reaction.emoji == RIGHT and cnum < lviewed:
            await edit_comic(reaction.message, cnum + 1)
        
        elif (reaction.emoji == RIGHT and cnum == lviewed and
                people[user.id]["name"] in readers and lviewed < latest and
                stime <= datetime.now().time() <= etime and
                date.today() != update):
            
            # Wow, that is a lot of conditions to check
            db_update(cnum + 1)
            await edit_comic(reaction.message, cnum + 1)
        
        await reaction.remove(user)
        await asyncio.sleep(0.5) # So the reactions can't get spammed
    
    elif reaction.emoji == DELETE:
        await reaction.message.delete()
