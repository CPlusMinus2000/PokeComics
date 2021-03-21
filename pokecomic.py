#!/usr/bin/python3
import os

import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
from glob import glob
from update import comicdata, NUM_DIGITS

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

# Apparently Discord now requires bots to have priveleged intentions
intents = discord.Intents.all()
# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$p', intents=intents)

# This is really just a tutorial function (just produces output)
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([f"{member.name} {member.id}" for member in guild.members])
    print(f'Guild Members:\n - {members}')

# This is the real meat of the bot
@bot.command(name="comic", help="Sends a comic.")
async def comic(ctx, content: str):
    
    pingers = {
        414630128602054658: "Colin",
        624152786392842281: "Claudine",
        222084166232047616: "William",
        690682574686650459: "Jessica",
        453350283242897430: "Oliver",
        690682526997676102: "Cynthia",
        690683382681829418: "Brianna",
        275699575556407297: "Nick",
        285333440948338699: "Daniel"
    }
    
    channels = ["comics"]

    if ctx.message.channel.name in channels:
        # await message.channel.send("Hi!")
        content = content.strip()

        # Check the comic number requested
        if content[:3].isdigit() and len(content[:3]) >= 3:
            comics = glob(f"Comics/{content[:3]}*")
            if len(comics) >= 1 and content.endswith('t'):
                await ctx.send(file=discord.File(comics[0]))

            elif len(comics) >= 1:
                name = os.path.splitext(comics[0])[0] + ".png"
                if not os.path.exists(name):
                    os.system(f'convert "{comics[0]}" "{name}" > /dev/null')
                
                await ctx.send(file=discord.File(name))

            else:
                await ctx.send(
                    "A comic with that number does not exist. Sorry!")
        
        elif "latest" in content:
            latest = comicdata.find_one({"latest": {"$exists": True}})["latest"]
            try:
                comic = glob(f"Comics/{str(latest).zfill(NUM_DIGITS)}*")[0]
                name = os.path.splitext(comic)[0] + ".png"
                if not os.path.exists(name):
                    os.system(f'convert "{comic}" "{name}" > /dev/null')
                
                await ctx.send(file=discord.File(name))
            except:
                print(latest)
        
        elif "rand" in content:
            comic = random.sample(glob("Comics/*"), 1)[0]
            name = os.path.splitext(comic)[0] + ".png"
            if not os.path.exists(name):
                os.system(f'convert "{comic}" "{name}" > /dev/null')

            await ctx.send(file=discord.File(name))
        
        else:
            await ctx.send("Unknown command. Please try again.")

bot.run(TOKEN)
