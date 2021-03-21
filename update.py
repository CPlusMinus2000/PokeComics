#!/usr/bin/python3

import pymongo
import os

from glob import glob
from datetime import datetime

NUM_DIGITS = 3

# Database variables
dbuser = "hcolin88"
dbpass = "Zb1IVRQc6lt9vvqj"
dbhost = "cluster0.fbzdw.mongodb.net"
dbname = "myFirstDatabase"
dbopts = "retryWrites=true&w=majority"

entry = f"mongodb+srv://{dbuser}:{dbpass}@{dbhost}/{dbname}?{dbopts}"
client = pymongo.MongoClient(entry)
comicdb = client.Pokecomics
comicdata = comicdb.comics

# Update script to push new comic information into the database
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
            "published": datetime.today().isoformat()
        })

# Add the numeric value of the latest comic
comicdata.replace_one({"latest": {"$exists": True}}, {"latest": latest}, True)
