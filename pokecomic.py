#!/usr/bin/python3
import os
import discord
import random
import json
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from glob import glob

from update import NUM_DIGITS as ND
from pokeapi import Pokemon, special_cases
from dexload import MAX_POKEMON

from modules.database import get_metadata, update_members
from modules.misc import *
from modules.comic import *
from modules.silly import *
from modules.dialogue import dialogue
from modules.emojis import emojis
from words.words import words

# Some Discord authentication information
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

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

DAILY_WAIT = timedelta(hours = 23)

# Some setup printouts, plus extra info in case I need to scrape something
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    await bot.change_presence(activity=discord.Game(name="Voltorb Flip"))

    if False: # This exists so I can regenerate the members list
        members = get_metadata("members")
        for g in bot.guilds:
            for m in g.members:
                members[str(m.id)] = {
                    "name": m.name,
                    "daily": datetime.min.isoformat(),
                    "streak": 0,
                    "points": 100
                }
        
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
    user = message.author.id
    if listen and people[user]["name"] in authorized and 'y' in cont:
        await send_comic(message.channel, get_metadata("lviewed"))
    
    elif listen and people[user]["name"] in authorized and 'n' in cont:
        await message.channel.send("Understood.")
    
    elif cont == "good bot":
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
    
    embeds = reaction.message.embeds
    if SITE in reaction.message.content:
        await process_reaction_comic(reaction, user)
    
    elif embeds and embeds[0].title.startswith("Poll:"):
        pass # Maybe one day I'll do something with this
    

@bot.event
async def on_command_error(ctx, error):
    errors = (
        commands.errors.CommandInvokeError,
        commands.errors.UnexpectedQuoteError,
        commands.errors.InvalidEndOfQuotedStringError
    )
    
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"{str(error)}. Maybe try $phelp?")
        return
    
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        parts = ctx.message.content.split(' ')
        if parts[0] == "$p":
            command = parts[1]
        else:
            command = parts[0][2:]
        
        await ctx.send(f"{error} Try using $phelp {command}?")
        return
    
    elif isinstance(error, errors):
        await ctx.send(str(error))
        return
    
    raise error

# This is the real meat of the bot
@bot.command(name="comic", help=dialogue["comic_help"])
async def comic(ctx, content: str):
    global listen

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
            if people[ctx.author.id]["name"] in authorized:
                listen = True
                await ctx.send(dialogue["comic_sure"])
            
            elif people[ctx.author.id]["name"] in readers:
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
        if (people[ctx.author.id]["name"] in readers and lv < lat and
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
        await send_comic(ctx, random.randint(1, lv))
    
    else:
        await ctx.send(dialogue["comic_unrecognized"] % content)


@bot.command(name="latest", help=dialogue["latest_help"])
async def latest(ctx):
    lv = get_metadata("lviewed")
    lat = get_metadata("latest")
    update = get_date("updated")
    stime, etime = bounds()

    if (people[ctx.author.id]["name"] in readers and lv < lat and
        stime <= datetime.now().time() <= etime and update != date.today()):
            
        db_update(lv + 1)
        await ctx.send(dialogue["comic_wake"])
        await send_comic(ctx, lv + 1)

    else:
        await send_comic(ctx, lv)
        if lat > lv and people[ctx.author.id]["name"] in readers:
            await ctx.send(dialogue["comic_hiding"])

        elif lat > lv:
            await ctx.send(dialogue["comic_hiding_else"])


@bot.command(name="status", help=dialogue["status_help"])
async def status(ctx):
    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send(dialogue["status_msg"] % (lview, latest))


@bot.command(name="statsu", help=dialogue["statsu_help"])
async def statsu(ctx):
    latest, lview = get_metadata("latest"), get_metadata("lviewed")
    await ctx.send(dialogue["statsu_msg"] % (lview, latest))


@bot.command(name="search", help=dialogue["search_help"])
async def search(ctx, *keywords):
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


TIME_CONVERT = 3
@bot.command(name="rules", help=dialogue["rules_help"])
async def rules(ctx):
    wkt, wet = bounds(0)[1], bounds(5)[1]
    wkform = f"{wkt.hour - TIME_CONVERT}:{wkt.minute}"
    weform =  f"{wet.hour - TIME_CONVERT}:{wet.minute}"
    await ctx.send(dialogue["rules_msg"] % (wkform, weform))


@bot.command(name="okedex", help=dialogue["dex_help"])
async def pic(ctx, *args):
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
    if info.form is not None:
        title += f" - {' '.join(info.form.split('-')[1:]).title()}"
    
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
    entry.add_field(name="Type(s)", value=typeinfo)
    entry.add_field(name="Abilities", value='\n'.join(info.get_abilities()))
    
    cr = "https://bulbapedia.bulbagarden.net/wiki/Catch_rate"
    entry.add_field(name="Catch Rate", value=f"[{info.capture}]({cr})")
    entry.add_field(name="Height/Weight", value=info.get_size())
    entry.add_field(name="Characters", value=','.join(info.characters))
    entry.add_field(name="Gender Ratio", value=info.format_gender())
    
    entry.set_footer(text=info.get_flavour())
    await ctx.send(embed=entry)


@bot.command(name="daily", help=dialogue["daily_help"])
async def daily(ctx):
    last_checked = datetime.fromisoformat(people[ctx.author.id]["daily"])
    if datetime.today() - last_checked >= DAILY_WAIT:
        people[ctx.author.id]["daily"] = datetime.today().isoformat()
        people[ctx.author.id]["points"] += 50
        if (datetime.today() - last_checked).days <= 1:
            people[ctx.author.id]["streak"] += 1
        else:
            people[ctx.author.id]["streak"] = 0

        await ctx.send(dialogue["daily_success"])
        update_members(people)
    
    else:
        wt = (DAILY_WAIT - (datetime.today() - last_checked)).seconds
        h, m, s = wt // 3600, (wt % 3600 // 60), wt % 60
        wat = (h, 's' * (h != 1), m, 's' * (m != 1), s, 's' * (s != 1))
        await ctx.send(dialogue["daily_fail"] % wat)


@bot.command(name="balance", help=dialogue["balance_help"])
async def balance(ctx):
    mention = f"<@{ctx.author.id}>"
    points = people[ctx.author.id]["points"]
    await ctx.send(dialogue["balance_msg"] % (mention, points))


@bot.command(name="words", help=dialogue["words_help"])
async def word(ctx, spec: str, content: str, *options):
    """
    Processes a fact purchase, for some extra comic details.

    Parameters
    ----------
    spec : str
        The category of the fact requested.
    
    content : str
        The number of the fact requested, or a specifying command (i.e. rand).
    
    options : Iterable[str]
        Some helpful options for certain commands, i.e., whether or not
        a new or old command is wanted for random generation.
    """

    if spec not in words:
        await ctx.send(dialogue["words_fail"])
        return

    seen = people[ctx.author.id]["facts"][spec]
    if content.isdigit():
        num = int(content)
        if num <= 0 or num > len(words[spec]):
            await ctx.send(dialogue["words_oob"] % (content, len(words[spec])))
        else:
            if len(seen) < len(words[spec]):
                seen += [False] * (len(words[spec]) - len(seen))

            if not seen[num - 1] and people[ctx.author.id]["points"] < 100:
                await ctx.send(dialogue["words_poor"])
                return
            elif not seen[num - 1]:
                people[ctx.author.id]["points"] -= 100
                seen[num - 1] = True

            await ctx.send(words[spec][num - 1])
    
    elif "rand" in content:
        if not options:
            await ctx.send(dialogue["words_no_options"])
        elif "new" in options[0] and people[ctx.author.id]["points"] < 100:
            await ctx.send(dialogue["words_poor"])
            return
        elif "new" in options[0]:
            unseen = [n for n in range(len(seen)) if not seen[n]]
            if not unseen:
                await ctx.send(dialogue["words_seen_all"])
            else:
                num = random.sample(unseen, 1)[0]
                people[ctx.author.id]["points"] -= 100
                seen[num - 1] = True
                await ctx.send(words[spec][num])
        elif "old" in options[0]:
            haveseen = [n for n in range(len(seen)) if seen[n]]
            if not haveseen:
                await ctx.send(dialogue["words_seen_all"])
            else:
                num = random.sample(haveseen, 1)[0]
                await ctx.send(words[spec][num])
        
        else:
            await ctx.send(dialogue["words_no_options"])
    
    else:
        await ctx.send(dialogue["words_unrecognized_content"])
    
    update_members(people)


@bot.command(name="erview", help="Checks which facts you have received.")
async def perview(ctx, *specs):
    """
    Displays which facts have already been asked for.
    """

    if not specs:
        specs = ("details", "lore", "references")
    else:
        for spec in specs:
            if spec not in words:
                await ctx.send(dialogue["words_fail"] % spec)

    viewed = discord.Embed(title="Viewed", color=COLOURS["gray"])
    for sp in specs:
        seen = people[ctx.author.id]["facts"][sp]
        fs = [str(n + 1) for n in range(len(seen)) if seen[n]]
        if fs:
            s = 's' if len(fs) > 1 else ''
            nums = ', '.join(fs[:-1])
            comma = ',' if len(fs) > 2 else ''
            info = f"{nums}{comma} and {fs[-1]}" if len(fs) > 1 else fs[0]
            viewed.add_field(name=sp.title(), 
                value=dialogue["pv_pos"] % (sp, s, info, len(words[sp])))
        else:
            viewed.add_field(name=sp.title(), value=dialogue["pv_zero"] % sp)
    
    await ctx.send(embed=viewed)


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

@bot.command(name="oll", help="Organizes a poll.")
async def oll(ctx, *info):
    """
    Makes a poll with a given question and some answers.
    """

    qwords = []
    answers = []
    marked = False
    curr = []
    for word in info:
        if marked and word == '|':
            answers.append(' '.join(curr))
            curr = []
        elif marked:
            curr.append(word)
        else:
            marked = True if '?' in word else False
            qwords.append(word)
    
    if curr:
        answers.append(' '.join(curr))

    if not answers:
        answers = ["Yes", "No"]
    
    title = f"Poll: {' '.join(qwords)}"
    poll = discord.Embed(title=title, color=COLOURS["black"])
    for i, answer in enumerate(answers):
        poll.add_field(
            name=chr(i + ord('A')), value=f"```{answer}```", inline=False
        )

    sent = await ctx.send(embed=poll)
    for i in range(len(answers)):
        await sent.add_reaction(emojis[chr(i + ord('A'))])


@bot.command(name="ython", help="Does Python evaluation.")
async def ython(ctx, *args):
    await bot_eval(ctx, *args)

if __name__ == "__main__":
    bot.run(TOKEN)
