# Shop module functions

import discord
import asyncio
import random
import os

from discord.ext.commands import Context
from modules.database import get_comic, get_comics, people, update_members
from modules.dialogue import dialogue
from modules.config import PURCHASE_FIELDS, RPHONE_TOPICS, RPHONE_TOPICS_PAID
from modules.config import COLOURS, NUM_DIGITS as ND, SLOT_INFO, SLOT_FAIL
from modules.config import SLOTS_PRICE
from typing import List, Tuple, Dict
from words.words import words
from glob import glob


IMAGE_WIDTH = 1200
CONVERT = f'convert "%s" -resize {IMAGE_WIDTH} "%s" &> /dev/null'

WORDS = {"fact", "facts"}
RPHONE = {"rphone"}
ALL_TOPICS = WORDS | RPHONE

PRICE = 100
SLOTS_MULTIPLIER = 7

def charge(people, user: discord.User, price: int, info: str) -> str:
    """
    Charges the user for a purchase, or returns an error message
    if the purchase couldn't go through.
    """

    if user.id not in people:
        raise ValueError("User not in database")
    
    if people[user.id]["points"] < price:
        balance = people[user.id]["points"]
        return dialogue["shop_poor"] % (user.mention, price, balance)
    else:
        people[user.id]["points"] -= price
        update_members(people)
        return ""  # Empty string signifies success, since it's falsy

async def shop(ctx, spec: str, content: str, *options):
    """
    Processes a purchase, at the cost of some points.


    Parameters
    ----------
    spec : str
        The category of the item requested.

    content : str
        Some additional specification information.

    options : Iterable[str]
        Some helpful options for certain commands, i.e., the number
        of a requested fun fact.
    """

    if spec.lower() not in ALL_TOPICS:
        await ctx.send(dialogue["spec_fail"] % spec)
        return

    elif spec.lower() in WORDS:
        if content not in words or not options:
            opts = '' if not options else ' ' + ' '.join(options)
            await ctx.send(
                dialogue["shop_fail"] % (spec, content, opts)
            )

            return

        seen = people[ctx.author.id]["facts"][content]
        if options[0].isdigit():
            num = int(options[0])
            if num <= 0 or num > len(words[content]):
                await ctx.send(
                    dialogue["words_oob"] % (content, len(words[content]))
                )

                return

            if len(seen) < len(words[content]):
                seen += [False] * (len(words[content]) - len(seen))
           
            if not seen[num - 1]:
                msg = charge(people, ctx.author, PRICE, "fact")
                if msg:
                    await ctx.send(msg)
                    return
                else:
                    seen[num - 1] = True

            await ctx.send(words[content][num - 1])

        elif "rand" in options[0]:
            if len(options) < 2:
                await ctx.send(dialogue["words_no_options"])
            elif "new" in options[1] and people[ctx.author.id]["points"] < 100:
                await ctx.send(dialogue["words_poor"])
                return
            elif "new" in options[1]:
                unseen = [n for n in range(len(seen)) if not seen[n]]
                if not unseen:
                    await ctx.send(dialogue["words_seen_all"])
                else:
                    num = random.sample(unseen, 1)[0]
                    people[ctx.author.id]["points"] -= 100
                    seen[num - 1] = True
                    await ctx.send(words[content][num])
            elif "old" in options[1]:
                haveseen = [n for n in range(len(seen)) if seen[n]]
                if not haveseen:
                    await ctx.send(dialogue["words_seen_all"])
                else:
                    num = random.sample(haveseen, 1)[0]
                    await ctx.send(words[content][num])

            else:
                await ctx.send(dialogue["words_no_options"])

        else:
            await ctx.send(dialogue["words_unrecognized_content"])

    elif spec.lower() in RPHONE:
        if content not in RPHONE_TOPICS or not options:
            opts = '' if not options else ' ' + ' '.join(options)
            await ctx.send(
                dialogue["shop_fail"] % (spec, content, opts)
            )

            return
        
        elif content.lower() == "main":
            # Look for main comics
            ident = options[0]
            if options[0].isdigit():
                ident = ident.zfill(ND)
            
            clink = glob(f"Comics/r*{ident}*.tif")
            clink = [  # Remove any paid-only comics
                c for c in clink if c.split('/')[1][:2] in RPHONE_TOPICS_PAID
            ]

            if not clink:
                await ctx.send(dialogue["rphone_no_comic"])
                return
            
            pcomic = os.path.splitext(clink[0])[0] + ".png"
            if not os.path.isfile(pcomic):
                os.system(CONVERT % (clink[0], pcomic))
                os.system(f'chmod a+rx "{pcomic}"')

            await ctx.send(file=discord.File(pcomic))
        
        else:
            # Purchase time
            seen = people[ctx.author.id]["rphone"][content]
            if options[0].isdigit():
                num = int(options[0])
                tag = f"r{RPHONE_TOPICS[content.lower()]}"
                com = get_comic(num, tag)
                if com is None:
                    await ctx.send(dialogue["rphone_no_comic"])
                    return
                
                if len(seen) < com["nr"]:
                    seen += [False] * (com["nr"] - len(seen))
                
                if not seen[num]:
                    msg = charge(people, ctx.author, PRICE, "rphone")
                    if msg:
                        await ctx.send(msg)
                        return
                    else:
                        seen[num] = True
                
                snum = str(num).zfill(ND)
                base = f"Comics/{tag}{snum} - {com['name']}"
                pcomic = base + ".png"
                if not os.path.isfile(pcomic):
                    orig = base + com["extension"]
                    os.system(CONVERT % (orig, pcomic))
                    os.system(f'chmod a+rx "{pcomic}"')

                    # Sleep for a bit to let the image load
                    await asyncio.sleep(2)
                
                await ctx.send(file=discord.File(pcomic))

    update_members(people)


async def purchased(ctx, topics: Dict[str, List[str]]):
    """
    Displays some information about your purchase history.
    """

    for topic in topics:
        if topic.lower() not in ALL_TOPICS:
            await ctx.send(dialogue["spec_fail"] % topic)
            return
        
        for spec in topics[topic]:
            if spec not in PURCHASE_FIELDS[topic.lower()]:
                await ctx.send(dialogue["spec_fail"] % spec)
                return

    content_type = "item"
    viewed = discord.Embed(
        title="Purchased",
        description=dialogue["shop_price"] % (content_type, PRICE),
        color=COLOURS["gray"]
    )

    for topic in topics:
        for sp in topics[topic]:
            seen = people[ctx.author.id][topic][sp]
            fs = [
                str(n + (topic.lower() in WORDS))
                for n in range(len(seen)) if seen[n]
            ]
            amt = len(words[sp]) if topic.lower() in WORDS else sum(
                1 for c in get_comics(tag=f"r{RPHONE_TOPICS[sp]}")
            )

            if fs:
                # Have to do a bunch of fancy stuff here to get grammar right
                s = 's' if len(fs) > 1 else ''
                nums = ', '.join(fs[:-1])
                comma = ',' if len(fs) > 2 else ''
                info = f"{nums}{comma} and {fs[-1]}" if len(fs) > 1 else fs[0]
                viewed.add_field(
                    name=sp.title(),
                    value=dialogue["pv_pos"] % (
                        sp, content_type, s, info, amt
                    )
                )
            
            else:
                viewed.add_field(
                    name=sp.title(), 
                    value=dialogue["pv_zero"] % (sp, content_type, amt)
                )

    await ctx.send(embed=viewed)


def spin_slots(reels: int, emojis, nice: bool=True) -> Tuple[str, List[str]]:
    """
    Spins the slots! Returns the result and the list of symbols.
    """

    spun = []
    for i in range(reels):
        reel = random.choice(list(SLOT_INFO.keys()))
        if len(spun) > 0 and reel != spun[-1] and nice:
            # Increase the odds of winning slightly
            reel = random.choice(list(SLOT_INFO.keys()))
        
        spun.append(reel)
    
    result = spun[0] if all(r == spun[0] for r in spun) else SLOT_FAIL
    symbols = [
        str(discord.utils.get(emojis, name=f"slots_{r}")) for r in spun
    ]
    return spun, result, symbols

async def play_slots(ctx: Context, emojis, slots: int=3):
    """
    Plays some slots!
    """

    prize_multiplier = SLOTS_MULTIPLIER ** (slots - 3)
    pay_multiplier = 1
    extra = ""
    if slots < 1:
        await ctx.send(dialogue["slots_oob"])
        return
    elif slots > 25:
        await ctx.send(dialogue["slots_many"])
        return
    elif slots < 3:
        pay_multiplier = prize_multiplier = 0
        extra = " Except you didn't, because there aren't enough reels."
    
    # Charge the user
    msg = charge(
        people, ctx.author, SLOTS_PRICE * pay_multiplier, "round of slots"
    )
    if msg:
        await ctx.send(msg)
        return
    
    # Spin up the slots
    play = True
    while play:
        _, result, symbols = spin_slots(slots, emojis)
        await ctx.send(''.join(symbols))
        play = False
        if result == SLOT_FAIL:
            await ctx.send(dialogue["slots_fail"])
            break
        elif result == "replay":
            play = True
        
        prize = SLOT_INFO[result]
        await ctx.send(random.choice(dialogue["slots_win"]) % prize + extra)
        people[ctx.author.id]["points"] += prize * prize_multiplier
    
    update_members(people)
