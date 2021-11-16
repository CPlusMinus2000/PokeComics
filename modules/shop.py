# Shop module functions

import discord
import random
import os

from modules.database import get_comic, get_comics, people, update_members
from modules.dialogue import dialogue
from modules.config import RPHONE_TOPICS, RPHONE_TOPICS_PAID
from modules.config import COLOURS, NUM_DIGITS as ND
from words.words import words
from glob import glob


IMAGE_WIDTH = 1200
CONVERT = f'convert "%s" -resize {IMAGE_WIDTH} "%s" &> /dev/null'

WORDS = {"fact", "facts"}
RPHONE = {"rphone"}
ALL_TOPICS = WORDS | RPHONE

PRICE = 100

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

            if not seen[num - 1] and people[ctx.author.id]["points"] < 100:
                await ctx.send(dialogue["words_poor"])
                return

            elif not seen[num - 1]:
                people[ctx.author.id]["points"] -= 100
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
                
                if not seen[num] and people[ctx.author.id]["points"] < 100:
                    await ctx.send(dialogue["words_poor"])
                    return
                
                elif not seen[num]:
                    people[ctx.author.id]["points"] -= 100
                    seen[num] = True
                
                snum = str(num).zfill(ND)
                base = f"Comics/{tag}{snum} - {com['name']}"
                pcomic = base + ".png"
                if not os.path.isfile(pcomic):
                    orig = base + com["extension"]
                    os.system(CONVERT % (orig, pcomic))
                    os.system(f'chmod a+rx "{pcomic}"')
                
                await ctx.send(file=discord.File(pcomic))

    update_members(people)


async def purchased(ctx, topic: str, *specs):
    """
    Displays some information about your purchase history.
    """

    if topic.lower() not in ALL_TOPICS:
        await ctx.send(dialogue["spec_fail"] % topic)
        return
    elif topic.lower() in WORDS and not specs:
        specs = ["details", "lore", "references"]
    elif topic.lower() in RPHONE and not specs:
        specs = sorted(
            RPHONE_TOPICS_PAID,
            key=lambda x: "zzzzz" if x.lower() == "other" else x
        )
    else:
        topics = words if topic.lower() in WORDS else RPHONE_TOPICS_PAID
        for spec in specs:
            if spec not in topics:
                await ctx.send(dialogue["spec_fail"] % spec)
                return

    content_type = "comic" if topic.lower() in RPHONE else "fact"
    viewed = discord.Embed(
        title="Purchased",
        description=dialogue["shop_price"] % (content_type, PRICE),
        color=COLOURS["gray"]
    )

    for sp in specs:
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
