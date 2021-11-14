#!/usr/bin/python3

import pymongo
import os

from glob import glob
from dotenv import load_dotenv
from datetime import datetime
from typing import Callable
from modules.config import Member, NUM_DIGITS

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
    viewstats = comicdata.find_one({"name": "viewstats"})

    # Step two: update the members
    for id, member in viewstats["members"].items():
        if m_filter(id, member):
            # In-place modification
            modification(member)

    # Step three: send the update back
    comicdata.replace_one({"name": "viewstats"}, viewstats)

    # Step four: remember that you already made this function in database.py
    # but it's too late now


# Update script to push new comic information into the database
if __name__ == "__main__":
    latest = 0
    for comic in glob("Comics/*"):
        if not comic.split("/")[1][:NUM_DIGITS].isdigit():
            continue

        title = comic.split("/")[1]
        number = int(title[:NUM_DIGITS])
        name, extension = os.path.splitext(title[NUM_DIGITS:].strip())
        latest = max(latest, number)

        if name.startswith("-"):
            name = name[1:].strip()

        # Insert any new comics
        if not comicdata.find_one({"nr": number}):
            print(f"Inserting: {comic}")
            comicdata.insert_one(
                {
                    "nr": number,
                    "name": name,
                    "extension": extension,
                    "published": datetime.today().isoformat(),
                    "viewed": False,
                }
            )

    # Add the numeric value of the latest comic
    viewstats = comicdata.find_one({"name": "viewstats"})
    viewstats["latest"] = latest
    comicdata.replace_one({"name": "viewstats"}, viewstats, True)
