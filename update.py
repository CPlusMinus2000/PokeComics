#!/usr/bin/python3

import pymongo
import os

from glob import glob
from dotenv import load_dotenv
from datetime import datetime

NUM_DIGITS = 3

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

# Update script to push new comic information into the database
if __name__ == "__main__":
    latest = 0
    for comic in glob("Comics/*"):
        if not comic.split('/')[1][:NUM_DIGITS].isdigit(): continue

        title = comic.split('/')[1]
        number = int(title[:NUM_DIGITS])
        name, extension = os.path.splitext(title[NUM_DIGITS:].strip())
        latest = max(latest, number)

        if name.startswith('-'):
            name = name[1:].strip()

        # Insert any new comics
        if not comicdata.find_one({"nr": number}):
            comicdata.insert_one({
                "nr": number,
                "name": name,
                "extension": extension,
                "published": datetime.today().isoformat(),
                "viewed": False
            })

    # Add the numeric value of the latest comic
    viewstats = comicdata.find_one({"name": "viewstats"})
    viewstats["latest"] = latest
    comicdata.replace_one({"name", "viewstats"}, viewstats, True)
