#!/usr/bin/python3

import pymongo
import os

from glob import glob
from dotenv import load_dotenv
from datetime import datetime
from typing import Callable
from modules.config import RPHONE_HEADERS, Member, NUM_DIGITS as ND
from modules.config import MEMBERS, VIEWSTATS

load_dotenv()
# Database variables
dbuser = os.getenv("DBUSER")
dbpass = os.getenv("DBPASS")
dbhost = os.getenv("DBHOST")
dbname = os.getenv("DBNAME")
dbopts = os.getenv("DBOPTS")

entry = f"mongodb+srv://{dbuser}:{dbpass}@{dbhost}/{dbname}?{dbopts}"
client = pymongo.MongoClient(entry)
comicdb = client.Pokecomics
comicdata = comicdb.comics


def update_members_schema(
    modification: Callable[[Member], None],
    m_filter: Callable[[Member], bool] = lambda x, y: True,
) -> None:
    """
    Updates all members in the members list of the schema
    according to the modification rule that pass the filter.
    """

    # Step one: access members list
    members = comicdata.find_one(MEMBERS)

    # Step two: update the members
    for id, member in members.items():
        if m_filter(id, member):
            # In-place modification
            modification(member)

    # Step three: send the update back
    comicdata.replace_one(MEMBERS, members)

    # Step four: remember that you already made this function in database.py
    # but it's too late now


def get_header(comic_title: str) -> str:
    """
    Finds the header of the comic_title, i.e. any letters
    that may be prepending the number of the comic that indicate
    if the comic is of a special topic (i.e. rb001 for Rotom-Battle 001).

    If no header can be found, returns an empty string.
    """

    if all(not c.isdigit() for c in comic_title):
        return ""

    ind = next(i for i, c in enumerate(comic_title) if c.isdigit())
    return comic_title[:ind]


# Update script to push new comic information into the database
if __name__ == "__main__":
    latest = 0
    for comic in glob("Comics/*"):
        tag = "c"
        title = comic.split("/")[1]
        if not title[:ND].isdigit():
            # Might be a rotom comic. Let's check it.
            tag = get_header(title)
            title = title[len(tag) :]
            if tag not in RPHONE_HEADERS or not title[:ND].isdigit():
                # Nope, it's not a rotom comic.
                continue

        number = int(title[:ND])
        name, extension = os.path.splitext(title[ND:].strip())
        latest = max(latest, number)

        if name.startswith("-"):
            name = name[1:].strip()

        # Insert any new comics
        if not comicdata.find_one({"nr": number, "tag": tag}):
            print(f"Inserting: {comic}")
            comicdata.insert_one(
                {
                    "nr": number,
                    "name": name,
                    "extension": extension,
                    "tag": tag,
                    "published": datetime.today().isoformat(),
                    "viewed": False,
                }
            )

    # Add the numeric value of the latest comic
    viewstats = comicdata.find_one(VIEWSTATS)
    viewstats["latest"] = latest
    comicdata.replace_one(VIEWSTATS, viewstats, True)
