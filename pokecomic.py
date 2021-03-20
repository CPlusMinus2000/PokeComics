# bot.py
import os

import discord
import random
from dotenv import load_dotenv
from datetime import datetime
from glob import glob

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

# Apparently Discord now requires bots to have priveleged intentions
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# This is really just a tutorial function (just produces output)
@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # members = '\n - '.join([member.name for member in guild.members])
    # print(f'Guild Members:\n - {members}')

# This is the real meat of the bot
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    pingers = [414630128602054658, 624152786392842281]
    channels = ["comics"]

    if message.author.id in pingers and message.channel.name in channels:
        # await message.channel.send("Hi!")
        if message.content.startswith("!comic"):
            content = message.content[6:].strip()

            # Check the comic number requested
            if content[:3].isdigit() and len(content[:3]) >= 3:
                comics = glob(f"Comics/{content[:3]}*")
                if len(comics) >= 1:
                    await message.channel.send(file=discord.File(comics[0]))
                else:
                    await message.channel.send(
                        "A comic with that number does not exist. Sorry!")

client.run(TOKEN)
