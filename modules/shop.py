# Shop module functions

import discord
import random
import modules.config as config

from discord.ext.commands import Context
from modules.database import get_comic, get_comics, people, update_members
from modules.dialogue import dialogue
from typing import List, Tuple
from words.words import words
from glob import glob


WORDS = {"fact", "facts"}
RPHONE = {"rphone"}
ALL_TOPICS = WORDS | RPHONE
ALL_OPTIONS = set(config.PURCHASE_FIELDS.keys()) | config.ALL_TOPICS_PAID

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
        return dialogue["shop_poor"] % (user.mention, price, balance, info)
    else:
        people[user.id]["points"] -= price
        update_members(people)
        return ""  # Empty string signifies success, since it's falsy


async def shop(ctx: discord.ext.commands.Context, *options) -> None:
    """
    The new shop command, which processes purchases and purchase requests.
    """

    # Fill out abbreviations
    opts = tuple(
        config.SHOP_ABBREVS[o] if o in config.SHOP_ABBREVS else o.lower()
        for o in options
    )

    # Get the user and their points
    userid = ctx.author.id
    if userid not in people:
        raise ValueError("User not in database")
    elif opts and opts[0].lower() in ['h', "help"]:
        await ctx.send(dialogue["shop_help"])
        return
    elif opts and opts[0] not in ALL_OPTIONS:
        await ctx.send(dialogue["spec_fail"] % opts[0])
        return
    elif len(opts) >= 2 and opts[0] not in config.ALL_TOPICS_PAID:
        await ctx.send(dialogue["spec_unrecognized"] % opts[0])
        return

    if len(opts) < 2:
        # Not a purchase request. Process help information.
        fields = {}
        if len(opts) == 1:
            # Get the topic
            topic = opts[0]
            if topic in config.PURCHASE_FIELDS:
                fields.update({topic: config.PURCHASE_FIELDS[topic]})
            else:
                top = next(
                    t for t in config.PURCHASE_FIELDS
                    if topic in config.PURCHASE_FIELDS[t]
                )

                fields.update({top: [topic]})

        else:
            fields.update(config.PURCHASE_FIELDS)

        # Now that we know what fields to display, make the embed
        desc = ""
        if len(fields) == 1:
            field = next(iter(fields.keys()))
            nfield = config.FIELD_NAMES[field]
            desc = dialogue["shop_price"] % (nfield, config.PRICES[field])
        else:
            specs = []
            for field in fields:
                nfield = config.FIELD_NAMES[field]
                specs.extend([nfield, config.PRICES[field]])

            desc = dialogue["shop_price_all"] % tuple(specs)

        viewed = discord.Embed(
            title=f"Purchase History for {ctx.author}",
            description=desc,
            color=config.COLOURS["gray"]
        )

        for field in fields:
            for topic in fields[field]:
                seen = people[userid][field][topic]
                nfield = config.FIELD_NAMES[field]
                fs = [
                    f"#{n + (field.lower() == 'facts')}"
                    for n in range(len(seen)) if seen[n]
                ]

                amt = len(words[topic]) if field == "facts" else sum(
                    1 for c in get_comics(
                        tag=f"r{config.RPHONE_TOPICS[topic]}"
                    )
                )

                if fs:
                    # Have to do a bunch of stuff here to get grammar right
                    s = 's' if len(fs) > 1 else ''
                    nums = ', '.join(fs[:-1])
                    comma = ',' if len(fs) > 2 else ''
                    info = fs[0]
                    if len(fs) > 1:
                        info = f"{nums}{comma} and {fs[-1]}"

                    viewed.add_field(
                        name=topic.title(),
                        value=dialogue["pv_pos"] % (
                            topic, nfield, s, info, amt
                        )
                    )

                else:
                    viewed.add_field(
                        name=topic.title(),
                        value=dialogue["pv_zero"] % (topic, nfield, amt)
                    )

        await ctx.send(embed=viewed)

    elif opts[0] in words:
        seen = people[userid]["facts"][opts[0]]
        balance = people[userid]["points"]
        if opts[1].isdigit():
            num = int(opts[1])
            if num <= 0 or num > len(words[opts[1]]):
                await ctx.send(
                    dialogue["words_oob"] % (opts[1], len(words[opts[1]]))
                )

                return

            if len(seen) < len(words[opts[1]]):
                seen += [False] * (len(words[opts[1]]) - len(seen))

            if not seen[num - 1]:
                msg = charge(
                    people, ctx.author, config.PRICES["facts"], "fact"
                )

                if msg:
                    await ctx.send(msg)
                    return
                else:
                    seen[num - 1] = True

            await ctx.send(words[opts[1]][num - 1])

        elif "rand" in opts[1]:
            if len(opts) < 3:
                await ctx.send(dialogue["words_no_options"])
            elif "new" in opts[2] and balance < config.PRICES["facts"]:
                await ctx.send(dialogue["words_poor"])
                return
            elif "new" in opts[2]:
                unseen = [n for n in range(len(seen)) if not seen[n]]
                if not unseen:
                    await ctx.send(dialogue["words_seen_all"])
                else:
                    num = random.choice(unseen)
                    people[ctx.author.id]["points"] -= config.PRICES["facts"]
                    seen[num - 1] = True
                    await ctx.send(words[opts[1]][num])

            elif "old" in opts[2]:
                haveseen = [n for n in range(len(seen)) if seen[n]]
                if not haveseen:
                    await ctx.send(dialogue["words_seen_none"])
                else:
                    num = random.choice(haveseen)
                    await ctx.send(words[opts[1]][num])

            else:
                await ctx.send(dialogue["words_no_options"])

        else:
            await ctx.send(dialogue["words_unrecognized_content"])

    else:  # By my reckoning, this has to be a comic request
        if opts[0] == "main":
            ident = opts[1]
            if ident.isdigit():
                ident = ident.zfill(config.NUM_DIGITS)

            clink = glob(f"Comics/r*{ident}*.tif")
            clink = [  # Remove any paid-only comics
                c for c in clink
                if c.split('/')[1][:2] in config.RPHONE_TOPICS_PAID
            ]

            if not clink:
                await ctx.send(dialogue["rphone_no_comic"])
                return

            pcomic = config.create_png(clink[0], resize=True)
            await ctx.send(file=discord.File(pcomic))

        else:
            seen = people[ctx.author.id]["rphone"][opts[0]]
            if opts[1].isdigit():
                num = int(opts[1])
                tag = f"r{config.RPHONE_TOPICS[opts[0]]}"
                com = get_comic(num, tag)
                if com is None:
                    await ctx.send(dialogue["rphone_no_comic"])
                    return

                if len(seen) < com["nr"] + 1:
                    seen += [False] * (com["nr"] + 1 - len(seen))

                if not seen[num]:
                    msg = charge(
                        people, ctx.author, config.PRICES["rphone"], "rphone"
                    )

                    if msg:
                        await ctx.send(msg)
                        return
                    else:
                        seen[num] = True

                snum = str(num).zfill(config.NUM_DIGITS)
                name = f"Comics/{tag}{snum} - {com['name']}" + com["extension"]
                pcomic = config.create_png(name, resize=True)
                await ctx.send(file=discord.File(pcomic))

    update_members(people)


def spin_slots(reels: int, emojis, nice: bool=True) -> Tuple[str, List[str]]:
    """
    Spins the slots! Returns the result and the list of symbols.
    """

    spun = []
    for i in range(reels):
        reel = random.choice(list(config.SLOT_INFO.keys()))
        if len(spun) > 0 and reel != spun[-1] and nice:
            # Increase the odds of winning slightly
            reel = random.choice(list(config.SLOT_INFO.keys()))
        
        spun.append(reel)
    
    result = spun[0] if all(r == spun[0] for r in spun) else config.SLOT_FAIL
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
        people, ctx.author, 
        config.SLOTS_PRICE * pay_multiplier, "round of slots"
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
        if result == config.SLOT_FAIL:
            await ctx.send(dialogue["slots_fail"])
            break
        elif result == "replay":
            play = True
        
        prize = config.SLOT_INFO[result] * prize_multiplier
        await ctx.send(random.choice(dialogue["slots_win"]) % prize + extra)
        people[ctx.author.id]["points"] += prize
    
    update_members(people)
