#!/usr/bin/python3
import os, sys
import asyncio
import discord
import random
import json
import contextlib
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, date, time
from glob import glob
from update import client, comicdata, NUM_DIGITS as ND
from pokeapi import Pokemon, special_cases
from pathlib import Path
from typing import Union, Tuple, List
from io import StringIO

# Some Discord authentication information
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

# Place where I store all the comics
SITE = "https://student.cs.uwaterloo.ca/~cqhe/"

# Total number of Pokémon that have been discovered
MAX_POKEMON = 898

# Emojis for reactions
LEFT = '◀️'
RIGHT = '▶️'
PIPLUP_ID = 824140724224000020
SADPIP_ID = 825045713515315261
DELETE = '🗑️'

# File extensions that Discord can display directly
DISPLAY = (".png", ".PNG", ".jpg", ".jpeg", ".JPG", ".JPEG")

# Apparently Discord now requires bots to have priveleged intentions
intents = discord.Intents.all()
# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$p', intents=intents)

# Boolean for particular questions
listen = False

chelp = """
Sends a comic. There are some different options available:
 - `$pcomic NNN` sends the comic with number NNN (i.e. 003, 420, etc.).
 - `$pcomic NNNt` is similar, but sends a .tif rather than a .png.
 - `$pcomic NNNu` sends an uncoloured version of the comic.
 - `$pcomic latest` sends the latest comic that YOU have permission to view.
"""

# This is a dictionary of people in the server
people = json.load(open("members.json", 'r'))
people = {int(p): people[p] for p in people}

channels = [ # Channels that comics can be distributed in
    "comics", "botspam", "cs136-piazza-count-bet"
]

# List of authorized people
authorized = ["The20thIcosahedron"]

# List of readers
readers = ["claudineyip"]

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
def bounds() -> Tuple[time, time]:
    """Get the left/right bounds of when comics are available."""

    stime = time(8, 0, 0)
    day = date.today().weekday()
    etime = time(10, 35, 10, 10010) if day < 5 else time(11, 20, 20, 20020)
    
    return stime, etime

def db_update(comic_num: int) -> None:
    """
    Updates the database, specifically any entry related to comic_num.
    """

    # Replace the comic
    curr = comicdata.find_one({"nr": comic_num})
    curr["viewed"] = True
    comicdata.replace_one({"nr": comic_num}, curr)

    viewstats = comicdata.find_one({"name": "viewstats"})
    viewstats["lviewed"] = comic_num
    viewstats["updated"] = date.today().isoformat()

    # Update the latest viewstats
    comicdata.replace_one({"name": "viewstats"}, viewstats)


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

def get_metadata(field: str) -> int:
    """
    Gets the specific metadata value indicated by 'field'.
    """

    return comicdata.find_one({"name": "viewstats"})[field]

def get_date(field: str) -> date:
    """
    Gets the date given by the 'field' field in comicdata.viewstats.
    """

    update = comicdata.find_one({"name": "viewstats"})[field]
    return date(*map(int, update.split('-')))

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


@contextlib.contextmanager
def stdoutIO(stdout=None):
    """
    Does some stuff with input/output for exec.
    """

    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


async def send_comic(ctx, comic: Union[str, int], colour: bool = True):
    """
    Sends a comic, and also checks for possible necessary preparations.
    """

    if isinstance(comic, int):
        comic = fetch_comic(comic, colour)

    name = f"{str(Path.home())}/public_html/{os.path.splitext(comic)[0]}.png"
    if not os.path.exists(name):
        os.system(f'convert "{comic}" "{name}" > /dev/null')
        os.system(f"chmod a+rx '{name}'")

    #TODO: Replace 4 with an actual not-hardcoded index
    fname = '/'.join(name.split('/')[4:]).replace(' ', "%20")
    msg = await ctx.send(f"{SITE}{fname}")
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
    await msg.add_reaction(bot.get_emoji(PIPLUP_ID))
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


# Some setup printouts, plus extra info in case I need to scrape something
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # members = '\n'.join([f"{m.name} {m.id}" for m in guild.members])
    # print(f'Guild Members:\n - {members}')

    if False: # This exists so I can regenerate the members list
        members = {}
        for g in bot.guilds:
            for m in g.members:
                members[m.id] = m.name
        
        with open("members.json", 'w') as f:
            json.dump(members, f, indent=4, sort_keys=True)
    
    # print(list(guild.emojis))

@bot.event
async def on_message(message):
    global listen
    if message.author == bot.user:
        return
    
    if bot.user.mentioned_in(message) and "everyone" not in message.content:
        await message.channel.send("Hi! What can I do for you?")
    
    cont = message.content.lower()
    if listen and people[message.author.id] in authorized and 'y' in cont:
        await send_comic(message.channel, get_metadata("lviewed"))
    
    elif listen and people[message.author.id] in authorized and 'n' in cont:
        await message.channel.send("Understood.")
    
    elif message.channel in channels and cont == "good bot":
        await message.reply(content="Thanks! I try my best.")
    
    listen = False
    if message.content.startswith("$p "):
        message.content = "$p" + message.content[2:].lstrip()
    
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author != bot.user or user == bot.user:
        # Ignore other people's messages, and own reactions
        return
    
    cont = reaction.message.content
    if SITE in cont and reaction.emoji in [LEFT, RIGHT]: 
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
                people[user.id] in readers and lviewed < latest and
                stime <= datetime.now().time() <= etime and
                date.today() != update):
            
            # Wow, that is a lot of conditions to check
            db_update(cnum + 1)
            await edit_comic(reaction.message, cnum + 1)
        
        await reaction.remove(user)
        await asyncio.sleep(0.5) # So the reactions can't get spammed
    
    elif SITE in cont and reaction.emoji == DELETE:
        await reaction.message.delete()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"{str(error)}. Maybe try $phelp?")
        return
    
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send(str(error))
        return
    
    elif isinstance(error, commands.errors.UnexpectedQuoteError):
        await ctx.send(str(error))
        return
    
    elif isinstance(error, commands.errors.InvalidEndOfQuotedStringError):
        await ctx.send(str(error))
        return
    
    raise error

# This is the real meat of the bot
@bot.command(name="comic", help=chelp)
async def comic(ctx, content: str):
    global listen
    if ctx.message.channel.name not in channels:
        return

    # await message.channel.send("Hi!")
    content = content.strip()
    lv = get_metadata("lviewed")
    lat = get_metadata("latest")
    present = datetime.now().time()
    update = get_date("updated")
    stime, etime = bounds()

    # Check the comic number requested
    if content[0].isdigit():

        # Get some relevant information
        cnum = leading_num(content)
        comics = glob(f"Comics/{str(cnum).zfill(ND)}*")
        if len(comics) >= 1 and cnum > lv + 1:
            await ctx.send("You don't have permission to access that comic.")
        
        elif len(comics) >= 1 and cnum == lv + 1:
            if people[ctx.author.id] in authorized:
                listen = True
                await ctx.send(
                    "Are you sure you want to release a new comic? (y/n)"
                )
            
            elif people[ctx.author.id] in readers:
                if stime <= present <= etime and update != date.today():
                    db_update(cnum)
                    await ctx.send("You woke up! Here's the next comic ^_^")
                    await send_comic(ctx, cnum)
                
                else:
                    await ctx.send("Sorry Clau. Now's not the right time.")
            
            else:
                await ctx.send("You don't have permission to read this.")
        
        elif len(comics) >= 1 and content.endswith('t'):
            tiff = next(c for c in comics if c.endswith("tif"))
            await ctx.send(file=discord.File(tiff))
        
        elif len(comics) >= 1 and content.endswith('u'):
            await send_comic(ctx, cnum, False)

        elif len(comics) >= 1:
            await send_comic(ctx, cnum)

        else:
            await ctx.send(
                "A comic with that number is not available (yet). Sorry!")
    
    # Command for fetching the latest comic
    elif "latest" in content:
        if (people[ctx.author.id] in readers and lv < lat and
            stime <= present <= etime and update != date.today()):
        
                db_update(lv + 1)
                await ctx.send("You woke up! Here's the next comic ^_^")
                await send_comic(ctx, lv + 1)
        
        else:
            await send_comic(ctx, lv)

            if lat > lv and people[ctx.author.id] in readers:
                await ctx.send(
                    ("Hi Clau! Colin already drew the next comic, "
                    "but you don't get to see it yet. Sorry!")
                )

            elif lat > lv:
                await ctx.send(
                    ("Colin has drawn a newer comic, "
                    "but it's not available yet. "
                    "Go bug Claudine if you want to read it.")
                )
    
    elif "rand" in content:
        number = random.randint(1, lv)
        await send_comic(ctx, number)
    
    else:
        await ctx.send(
            "I don't recognize that command -- can you try $phelp?"
        )


@bot.command(name="latest", help="Gets the latest comic.")
async def latest(ctx):
    if ctx.channel.name not in channels:
        return

    lv = get_metadata("lviewed")
    lat = get_metadata("latest")
    update = get_date("updated")
    stime, etime = bounds()

    if (people[ctx.author.id] in readers and update != date.today() and
        stime <= datetime.now().time() <= etime and lv < lat):
            
        db_update(lv + 1)
        await ctx.send("You woke up! Here's the next comic ^_^")
        await send_comic(ctx, lv + 1)

    else:
        await send_comic(ctx, lv)

        if lat > lv and people[ctx.author.id] in readers:
            await ctx.send(
                ("Hi Clau! Colin already drew the next comic, "
                "but you don't get to see it yet. Sorry!")
            )

        elif lat > lv:
            await ctx.send((
                "Colin has drawn a newer comic, "
                "but it's not available yet. "
                "Go bug Claudine if you want to read it."
            ))


@bot.command(name="status", help="Gets the current status of comics.")
async def status(ctx):
    if ctx.message.channel.name not in channels:
        return

    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send((
        f"{lview} comics have been viewed so far, "
        f"and #{latest} is the latest drawn."
    ))


@bot.command(name="statsu", help="コミックの現在のstatsuを取得します。")
async def statsu(ctx):
    if ctx.message.channel.name not in channels:
        return

    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send(
        f"これまでに{lview}冊の漫画が描かれ、最新の漫画は{latest}冊です。"
    )


@bot.command(name="gstatsu", help="Gives/removes G-statsu.")
async def gstatsu(ctx, name: str):
    # Probably want to have this take @'s?
    pass


@bot.command(name="search", help="Searches for a comic given some text.")
async def search(ctx, *keywords):
    if not ctx.message.channel.name in channels:
        return
    
    lview = get_metadata("lviewed")
    qtext = ' '.join(keywords)
    result = insensitive_glob(f"Comics/*{qtext}*.tif")
    comics = [c for c in result if valid_comic(c, lview) != -1]

    if not comics: # No comics found
        sad = f"<:sadpip:{SADPIP_ID}>"
        await ctx.send(f"I couldn't find any comics with that text. {sad}")
    elif len(comics) == 1:
        await send_comic(ctx, comics[0])
    else: # TODO: Make this display the list, and ask for a selection
        await send_comic(ctx, comics[0])


@bot.command(name="rules", help="States the rules of how comics work.")
async def rules(ctx):
    if ctx.message.channel.name not in channels:
        return

    await ctx.send((
        "Hi!!! It's ya bot here, comin' at you with a quick heads-up: "
        "The original intent behind Colin drawing these comics "
        "is to entice Claudine to wake up early in the mornings. "
        "Because of this, Colin decided to incentivize Claudine "
        "by letting her see a new strip of his not-a-fanfiction "
        "Pokémon comic when he draws them, but ONLY if she gets up "
        "early enough in the morning (specifically 5:00-7:35 PST).\n\n"
        "Because of this, the next comic might not be available yet, "
        "and it'll only come out when she gets up early enough. "
        "PokeComicsBot out!"
    ))


@bot.command(name="okedex", help="Gets a Pokédex entry of the Pokémon given.")
async def pic(ctx, *args):
    if ctx.message.channel.name not in channels:
        return
    
    pokemon = ' '.join(args)
    index = json.load(open("index.json", 'r'))
    if pokemon.isdigit():
        pokemon = int(pokemon)
        if pokemon > MAX_POKEMON or pokemon < 1:
            await ctx.send("Hm... I've never met a Pokémon with that number.")
            return

        pokemon = index[str(pokemon)]
    
    else:
        pokemon = special_cases(pokemon)
    
    info = Pokemon(pokemon.lower())
    pok = info.punctuate()
    poku = pok.replace(' ', '_')
    title = f"#{info.id} {pok}"
    url = f"https://bulbapedia.bulbagarden.net/wiki/{poku}_(Pok%C3%A9mon)"
    entry = discord.Embed(
        title=title, url=url, 
        description=info.get_genus(), 
        color=COLOURS[info.colour]
    )

    # Crap tons of info embedding
    guild = discord.utils.get(bot.guilds, name=GUILD)
    typemojis = [f"{discord.utils.get(guild.emojis, name=t)} {t.capitalize()}"
                    for t in info.get_types()]
    
    typeinfo = '\n'.join(typemojis)
    # typeinfo = '\n'.join(info.get_types(True))
    entry.set_thumbnail(url=info.get_sprite())
    entry.add_field(name="Type(s)", value=typeinfo, inline=True)
    entry.add_field(name="Abilities", value='\n'.join(
        info.get_abilities()), inline=True)
    
    cr = "https://bulbapedia.bulbagarden.net/wiki/Catch_rate"
    entry.add_field(name="Catch Rate", value=f"[{info.capture}]({cr})", 
        inline=True)
    
    entry.add_field(name="Height/Weight", value=info.get_size(), inline=True)
    entry.add_field(name="Characters", value=','.join(info.characters),
        inline=True)
    
    entry.add_field(name="Gender Ratio", value=info.format_gender(),
        inline=True)
    
    entry.set_footer(text=info.get_flavour())

    await ctx.send(embed=entry)


@bot.command(name="iazza", help="Gets the current Piazza post count for 136.")
async def piazza(ctx):
    meta = client.Piazza.meta
    highest = meta.find_one({"name": "meta"})["highest"] - 1
    await ctx.send(f"Currently, there are {highest} Piazza posts. Yikes!")


@bot.command(name="ipsum", help="Gets a bit of lorem ipsum text.")
async def ipsum(ctx, options: str = "s"):
    import lorem

    if options.startswith('s'):
        await ctx.send(lorem.sentence())
    elif options.startswith('p'):
        await ctx.send(lorem.paragraph())
    elif options.startswith('t'):
        await ctx.send(lorem.text())
    else:
        await ctx.send("I don't recog- I mean, Lorem ipsum dolor sit amet.")


@bot.command(name="", help="empty...")
async def empty(ctx):
    await ctx.send(random.sample([
        "...",
        "_wind blows_",
        "_crickets chirp_",
        "no thoughts, head empty",
        ""
    ], 1)[0])

DISALLOWED = ["quit(", "exit(", "eval(", "exec("]

@bot.command(name="ython", help="Does Python evaluation.")
async def bot_eval(ctx, *args):
    code = ' '.join(args)
    if any(d in code for d in DISALLOWED):
        sad = bot.get_emoji(SADPIP_ID)
        await ctx.send(f"Hey, that's not very nice {sad}")
    elif "TOKEN" not in code and "os." not in code:
        await ctx.send(str(eval(code, {}))[:2000])
    else:
        await ctx.send("Nice try, wise guy.")
    

@bot.command(name="ython2", help="Does Python execution.")
async def bot_exec(ctx, *args):
    code = ' '.join(args)
    if any(d in code for d in DISALLOWED):
        sad = bot.get_emoji(SADPIP_ID)
        await ctx.send(f"Hey, that's not very nice {sad}")
        return
    
    if "import" in code:
        await ctx.send("Sorry, no fun allowed.")
        return
    
    with stdoutIO() as s:
        try:
            exec(code, {})
        except:
            print("Something wrong with the code")
            raise
    
    await ctx.send(s.getvalue()[:2000])


if __name__ == "__main__":
    bot.run(TOKEN)
