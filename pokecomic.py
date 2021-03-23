#!/usr/bin/python3
import os

import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, time
from glob import glob
from update import comicdata, NUM_DIGITS as ND
from pathlib import Path

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

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
 - `$pcomic latest` sends the latest comic that YOU have permission to view.
"""

people = { # This is a dictionary of people in the server
    414630128602054658: "Colin",
    624152786392842281: "Claudine",
    222084166232047616: "William",
    690682574686650459: "Jessica",
    453350283242897430: "Oliver",
    753691662076608512: "Oliver",
    690682526997676102: "Cynthia",
    690683382681829418: "Brianna",
    275699575556407297: "Nick",
    285333440948338699: "Daniel",
    260128919380819970: "Terry",
    690727551567528048: "Jenny",
    740377202406981633: "Vicki",
    224999022568407041: "Dayou"
}

channels = [ # Channels that comics can be distributed in
    "comics", "botspam"
]

# List of authorized people
authorized = ["Colin"]

# List of readers
readers = ["Claudine"]

# Start and ending times (so morning comics can only be seen from 6:00-7:30)
#  but converted to E[SD]T because that's where I'm hosting the bot from
stime = time(8, 0, 0)
etime = time(10, 35, 10, 10)

def db_update(comic_num: int) -> None:
    """
    Updates the database, specifically any entry related to comic_num.
    """

    # Replace the comic
    curr = comicdata.find_one({"nr": comic_num})
    curr["viewed"] = True
    comicdata.replace_one({"nr": comic_num}, curr)

    # Update the latest viewed
    comicdata.replace_one(
        {"lviewed": {"$exists": True}}, {"lviewed": comic_num})


async def send_comic(ctx: discord.ext.commands.Context, comic: str):
    """
    Sends a comic, and also checks for possible necessary preparations.
    """

    name = f"{str(Path.home())}/public_html/{os.path.splitext(comic)[0]}.png"
    if not os.path.exists(name):
        os.system(f'convert "{comic}" "{name}" > /dev/null')
        os.system(f"chmod a+rx '{name}'")

    #TODO: Replace 4 with an actual not-hardcoded index
    fname = '/'.join(name.split('/')[4:]).replace(' ', "%20")
    embed = discord.Embed()
    embed.description = f"https://student.cs.uwaterloo.ca/~cqhe/{fname}"
    # await ctx.send(embed=embed)
    await ctx.send(f"https://student.cs.uwaterloo.ca/~cqhe/{fname}")


# This is really just a tutorial function (just produces output)
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # members = '\n - '.join([f"{member.name} {member.id}" for member in guild.members])
    # print(f'Guild Members:\n - {members}')


@bot.event
async def on_message(message):
    global listen
    if message.author == bot.user:
        return
    
    if (listen and people[message.author] in authorized and 
            'y' in message.content.lower()):
        
        lv = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]
        comic = glob(f"Comics/{str(lv).zfill(ND)}*")[0]
        name = os.path.splitext(comic)[0] + ".png"
        if not os.path.exists(name):
            os.system(f'convert "{comic}" "{name}" > /dev/null')
        
        await message.channel.send(file=discord.File(name))
    
    elif (listen and people[message.author] in authorized and 
            'n' in message.content.lower()):
        
        await message.channel.send("Understood.")
    
    listen = False
    await bot.process_commands(message)

# This is the real meat of the bot
@bot.command(name="comic", help=chelp)
async def comic(ctx, content: str):
    global listen
    if ctx.message.channel.name in channels:
        # await message.channel.send("Hi!")
        content = content.strip()

        # Check the comic number requested
        if content[:ND].isdigit() and len(content[:ND]) >= ND:

            # Get some relevant information, like the filename and
            #  lv, which tells us whether or not the comic is allowed
            #  to be released at this moment
            lv = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]
            comics = glob(f"Comics/{content[:ND]}*")
            cnum = int(content[:ND])
            
            if len(comics) >= 1 and cnum > lv + 1:
                await ctx.send(
                    "You don't have permission to access that comic.")
            
            elif len(comics) >= 1 and cnum == lv + 1:
                if people[ctx.author.id] in authorized:
                    listen = True
                    await ctx.send(
                        "Are you sure you want to release a new comic? (y/n)"
                    )
                
                elif people[ctx.author.id] in readers:
                    if stime <= datetime.now().time() <= etime:
                        name = os.path.splitext(comics[0])[0] + ".png"
                        if not os.path.exists(name):
                            os.system(
                                f'convert "{comics[0]}" "{name}" > /dev/null')
                
                        db_update(cnum)
                        await ctx.send("You woke up! Here's the next comic ^_^")
                        await ctx.send(file=discord.File(name))
                    
                    else:
                        await ctx.send(
                            "Sorry Clau. Now's not the right time.")
                
                else:
                    await ctx.send("You don't have permission to read this.")
            
            elif len(comics) >= 1 and content.endswith('t'):
                await ctx.send(file=discord.File(comics[0]))

            elif len(comics) >= 1:
                name = os.path.splitext(comics[0])[0] + ".png"
                if not os.path.exists(name):
                    os.system(f'convert "{comics[0]}" "{name}" > /dev/null')
                
                await ctx.send(file=discord.File(name))

            else:
                await ctx.send(
                    "A comic with that number is not available. Sorry!")
        
        # Command for fetching the latest comic
        elif "latest" in content:
            lv = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]
            lat = comicdata.find_one({"latest": {"$exists": True}})["latest"]

            if (people[ctx.author.id] in readers and
                stime <= datetime.now().time() <= etime):
                    
                    comic = glob(f"Comics/{str(lv + 1).zfill(ND)}*")[0]
                    name = os.path.splitext(comic)[0] + ".png"
                    if not os.path.exists(name):
                        os.system(f'convert "{comic}" "{name}" > /dev/null')
            
                    db_update(lv + 1)
                    await ctx.send("You woke up! Here's the next comic ^_^")
                    await ctx.send(file=discord.File(name))
            
            else:
                comic = glob(f"Comics/{str(lv).zfill(ND)}*")[0]
                await send_comic(ctx, comic)

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
            lv = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]
            number = random.randint(1, lv)
            comic = glob(f"Comics/{str(number).zfill(ND)}*")[0]
            await send_comic(ctx, comic)
        
        else:
            await ctx.send(
                "I don't recognize that command -- can you try $phelp?")


@bot.command(name="latest", help="Gets the latest comic.")
async def latest(ctx):
    if ctx.channel.name in channels:
        lv = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]
        lat = comicdata.find_one({"latest": {"$exists": True}})["latest"]

        if (people[ctx.author.id] == "Claudine" and
            stime <= datetime.now().time() <= etime):
                
                comic = glob(f"Comics/{str(lv + 1).zfill(ND)}*")[0]
                name = os.path.splitext(comic)[0] + ".png"
                if not os.path.exists(name):
                    os.system(f'convert "{comic}" "{name}" > /dev/null')

                db_update(lv + 1)
                await ctx.send("You woke up! Here's the next comic ^_^")
                await ctx.send(file=discord.File(name))

        else:
            comic = glob(f"Comics/{str(lv).zfill(ND)}*")[0]
            name = os.path.splitext(comic)[0] + ".png"
            if not os.path.exists(name):
                os.system(f'convert "{comic}" "{name}" > /dev/null')
            
            await ctx.send(file=discord.File(name))

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
    if ctx.message.channel.name in channels:
        latest = comicdata.find_one({"latest": {"$exists": True}})["latest"]
        lview = comicdata.find_one({"lviewed": {"$exists": True}})["lviewed"]

        await ctx.send((
            f"{lview} comics have been viewed so far, "
            f"and #{latest} is the latest drawn."
        ))


@bot.command(name="rules", help="States the rules of how comics work.")
async def rules(ctx):
    if ctx.message.channel.name in channels:
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


bot.run(TOKEN)
