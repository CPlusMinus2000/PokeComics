"""All the stuff for joke commands"""

import sys
import lorem
import contextlib
from io import StringIO
from update import client

SADPIP_ID = 825045713515315261

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

async def gstatsu(ctx, name: str):
    """
    Something about giving people G-status? Super weird...
    """

    # Probably want to have this take @'s?
    pass

async def piazza(ctx) -> None:
    """
    Current Piazza post count for CS 136.
    """

    meta = client.Piazza.meta
    highest = meta.find_one({"name": "meta"})["highest"] - 1
    await ctx.send(f"Currently, there are {highest} Piazza posts. Yikes!")


async def ipsum(ctx, options: str = "s"):
    """
    Random lorem ipsum words, because why not.
    """

    if options.startswith('s'):
        await ctx.send(lorem.sentence())
    elif options.startswith('p'):
        await ctx.send(lorem.paragraph())
    elif options.startswith('t'):
        await ctx.send(lorem.text())
    else:
        await ctx.send("I don't recog- I mean, Lorem ipsum dolor sit amet.")
    

DISALLOWED = ["import", "eval", "exec"]

async def bot_eval(ctx, *args):
    code = ' '.join(args)
    if any(d in code.replace("'", "").replace('"',"") for d in DISALLOWED):
        await ctx.send(f"Hey, that's not very nice <:sadpip:{SADPIP_ID}>")
        return

    if len(args) >= 1 and args[0] == "-e":
        print(code)
        code = code[3:]
        
        if "import" in code:
            await ctx.send("Sorry, no fun allowed.")
            return
        
        with stdoutIO() as s:
            try:
                exec(code, {})
            except SystemExit:
                await ctx.send("Ow... that hurt!")
                return
            except:
                print("Something wrong with the code")
                raise
    
        await ctx.send(s.getvalue()[:2000])
    
    else:
        if "TOKEN" not in code and "os." not in code:
            try:
                await ctx.send(str(eval(code, {}))[:2000])
            except SystemExit:
                await ctx.send("Ow... that hurt!")
        else:
            await ctx.send("Nice try, wise guy.")

