# Shop module functions

import discord
import random
import os

from modules.database import people, update_members
from modules.dialogue import dialogue
from modules.misc import COLOURS
from words.words import words
from update import NUM_DIGITS as ND
from glob import glob


RPHONE_TOPICS = {
    "main": "",
    "world": 'w',
    "battle": 'b',
    "people": 'p',
    "scitech": 's',
    "other": 'o'
}
IMAGE_WIDTH = 1200
CONVERT = f'convert "%s" -resize {IMAGE_WIDTH} "%s" > /dev/null'

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

    if spec.lower() not in ["word", "words", "rphone"]:
        await ctx.send(dialogue["spec_fail"] % spec)
        return

    elif spec.lower() in ["word", "words"]:
        if content not in words or not options:
            await ctx.send(
                dialogue["shop_fail"] % (spec, content, ' '.join(options))
            )

            return

        seen = people[ctx.author.id]["facts"][content]
        if options[0].isdigit():
            num = int(options[0])
            if num <= 0 or num > len(words[content]):
                await ctx.send(
                    dialogue["words_oob"] % (content, len(words[content]))
                )
            else:
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

    elif spec.lower() == "rphone":
        if content not in RPHONE_TOPICS or not options:
            await ctx.send(
                dialogue["rphone_fail"] % (spec, content, ' '.join(options))
            )

            return
        
        elif content.lower() == "main":
            # Look for main comics
            ident = options[0]
            if options[0].isdigit():
                ident = ident.zfill(ND)
            
            clink = glob(f"Comics/r*{ident}*.tif")
            if not clink:
                await ctx.send(dialogue["rphone_no_comic"])
                return
            
            pcomic = os.path.splitext(clink[0])[0] + ".png"
            if not os.path.isfile(pcomic):
                os.system(CONVERT % (clink[0], pcomic))
                os.system(f'chmod a+rx "{pcomic}"')

            await ctx.send(file=discord.File(pcomic))

    update_members(people)


async def perview(ctx, *specs):
    """
    Displays some information about facts.
    """

    if not specs:
        specs = ("details", "lore", "references")
    else:
        for spec in specs:
            if spec not in words:
                await ctx.send(dialogue["spec_fail"] % spec)

        return

    viewed = discord.Embed(title="Viewed", color=COLOURS["gray"])
    for sp in specs:
        seen = people[ctx.author.id]["facts"][sp]
        fs = [str(n + 1) for n in range(len(seen)) if seen[n]]
        if fs:
            s = 's' if len(fs) > 1 else ''
            nums = ', '.join(fs[:-1])
            comma = ',' if len(fs) > 2 else ''
            info = f"{nums}{comma} and {fs[-1]}" if len(fs) > 1 else fs[0]
            viewed.add_field(
                name=sp.title(),
                value=dialogue["pv_pos"] % (sp, s, info, len(words[sp]))
            )
        else:
            viewed.add_field(name=sp.title(), value=dialogue["pv_zero"] % sp)

    await ctx.send(embed=viewed)
