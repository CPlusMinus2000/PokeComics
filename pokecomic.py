#!/usr/bin/python3
import os
import discord
import random
import json
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, date
from glob import glob
from update import NUM_DIGITS as ND
from pokeapi import Pokemon, special_cases

from modules.database import get_metadata, update_members
from modules.misc import bounds, insensitive_glob, leading_num
from modules.comic import *
from modules.silly import *
from modules.dialogue import dialogue

# Some Discord authentication information
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

# Total number of Pokémon that have been discovered
MAX_POKEMON = 898

# Apparently Discord now requires bots to have priveleged intentions
intents = discord.Intents.all()
# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$p', intents=intents)

# Boolean for particular questions
listen = False

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


# Some setup printouts, plus extra info in case I need to scrape something
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    if False: # This exists so I can regenerate the members list
        members = {}
        for g in bot.guilds:
            for m in g.members:
                members[str(m.id)] = m.name
        
        update_members(members)
    
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
    
    await process_reaction(reaction, user)
    

@bot.event
async def on_command_error(ctx, error):
    errors = [
        commands.errors.CommandInvokeError,
        commands.errors.UnexpectedQuoteError,
        commands.errors.InvalidEndOfQuotedStringError
    ]
    
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"{str(error)}. Maybe try $phelp?")
        return
    
    elif any(isinstance(error, e) for e in errors):
        await ctx.send(str(error))
        return
    
    raise error

# This is the real meat of the bot
@bot.command(name="comic", help=dialogue["comic_help"])
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
            await ctx.send(dialogue["comic_high"])
        
        elif len(comics) >= 1 and cnum == lv + 1:
            if people[ctx.author.id] in authorized:
                listen = True
                await ctx.send(dialogue["comic_sure"])
            
            elif people[ctx.author.id] in readers:
                if stime <= present <= etime and update != date.today():
                    db_update(cnum)
                    await ctx.send(dialogue["comic_wake"])
                    await send_comic(ctx, cnum)
                
                elif stime <= present <= etime:
                    await ctx.send(dialogue["comic_same_day"])
                
                else:
                    await ctx.send(dialogue["comic_late"])
            
            else:
                await ctx.send(dialogue["comic_wrong_person"])
        
        elif len(comics) >= 1 and content.endswith('t'):
            tiff = next(c for c in comics if c.endswith("tif"))
            await ctx.send(file=discord.File(tiff))
        
        elif len(comics) >= 1 and content.endswith('u'):
            await send_comic(ctx, cnum, False)

        elif len(comics) >= 1:
            await send_comic(ctx, cnum)

        else:
            await ctx.send(dialogue["comic_unavailable"])
    
    # Command for fetching the latest comic
    elif "latest" in content:
        if (people[ctx.author.id] in readers and lv < lat and
            stime <= present <= etime and update != date.today()):
        
                db_update(lv + 1)
                await ctx.send(dialogue["comic_wake"])
                await send_comic(ctx, lv + 1)
        
        else:
            await send_comic(ctx, lv)

            if lat > lv and people[ctx.author.id] in readers:
                await ctx.send(dialogue["comic_hiding"])

            elif lat > lv:
                await ctx.send(dialogue["comic_hiding_else"])
    
    elif "rand" in content:
        number = random.randint(1, lv)
        await send_comic(ctx, number)
    
    else:
        await ctx.send(dialogue["comic_unrecognized"])


@bot.command(name="latest", help=dialogue["latest_help"])
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
        await ctx.send(dialogue["comic_wake"])
        await send_comic(ctx, lv + 1)

    else:
        await send_comic(ctx, lv)
        if lat > lv and people[ctx.author.id] in readers:
            await ctx.send(dialogue["comic_hiding"])

        elif lat > lv:
            await ctx.send(dialogue["comic_hiding_else"])


@bot.command(name="status", help=dialogue["status_help"])
async def status(ctx):
    if ctx.message.channel.name not in channels:
        return

    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send(dialogue["status_msg"] % (lview, latest))


@bot.command(name="statsu", help=dialogue["statsu_help"])
async def statsu(ctx):
    if ctx.message.channel.name not in channels:
        return

    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send(dialogue["statsu_msg"] % (lview, latest))


@bot.command(name="search", help=dialogue["search_help"])
async def search(ctx, *keywords):
    if not ctx.message.channel.name in channels:
        return
    
    lview = get_metadata("lviewed")
    qtext = ' '.join(keywords)
    result = insensitive_glob(f"Comics/*{qtext}*.tif")
    comics = [c for c in result if valid_comic(c, lview) != -1]

    if not comics: # No comics found
        await ctx.send(dialogue["search_fail"] % f"<:sadpip:{SADPIP_ID}>")
    elif len(comics) == 1:
        await send_comic(ctx, comics[0])
    else: # TODO: Make this display the list, and ask for a selection
        await send_comic(ctx, comics[0])


@bot.command(name="rules", help=dialogue["rules_help"])
async def rules(ctx):
    if ctx.message.channel.name not in channels:
        return

    await ctx.send(dialogue["rules_msg"])


@bot.command(name="okedex", help=dialogue["dex_help"])
async def pic(ctx, *args):
    if ctx.message.channel.name not in channels:
        return
    
    pokemon = ' '.join(args)
    with open("index.json", 'r') as ind:
        index = json.load(ind)
    
    if pokemon.isdigit():
        pokemon = int(pokemon)
        if pokemon > MAX_POKEMON or pokemon < 1:
            await ctx.send(dialogue["dex_fail"])
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


@bot.command(name="slots", help="Plays some slots!")
async def slots(ctx, slots: int = 3):
    await ctx.send(dialogue["construction"])


# A few joke commands
@bot.command(name="gstatsu", help="Gives/removes G-statsu.")
async def gs(ctx, name: str) -> None:
    await ctx.send(dialogue["construction"])

@bot.command(name="iazza", help="Gets the current Piazza post count for 136.")
async def piaz(ctx):
    await piazza(ctx)

@bot.command(name="ipsum", help="Gets a bit of lorem ipsum text.")
async def ips(ctx, options: str = "s"):
    await ipsum(ctx, options)

@bot.command(name="ython", help="Does Python evaluation.")
async def ython(ctx, *args):
    await bot_eval(ctx, *args)

if __name__ == "__main__":
    bot.run(TOKEN)
