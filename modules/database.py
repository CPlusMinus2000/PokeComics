"""Database interface functions."""

from typing import Dict
from update import client, comicdata, NUM_DIGITS as ND
from datetime import date

def db_update(comic_num: int) -> None:
    """
    Updates the database, specifically any entry related to comic_num.
    """

    # Replace the comic
    curr = comicdata.find_one({"nr": comic_num})
    curr["viewed"] = True
    comicdata.replace_one({"nr": comic_num}, curr)

    viewstats = comicdata.find_one({"name": "viewstats"})
    viewstats["lviewed"] = comic_num
    viewstats["updated"] = date.today().isoformat()

    # Update the latest viewstats
    comicdata.replace_one({"name": "viewstats"}, viewstats)


def get_metadata(field: str) -> int:
    """
    Gets the specific metadata value indicated by 'field'.
    """

    return comicdata.find_one({"name": "viewstats"})[field]


def set_metadata(field: str, value) -> None:
    """
    Sets the specific metadata value indicated by 'field'.
    """

    viewstats = comicdata.find_one({"name": "viewstats"})
    viewstats[field] = value
    comicdata.replace_one({"name": "viewstats"}, viewstats)


def update_members(members: Dict[str, str]) -> None:
    """
    Updates the members list in the database.
    NOTE: This function exhibits add-only behaviour. You can't
    overwrite old members.

    Parameters
    ----------
    members : dict[str, str]
        A dictionary of members, keyed by Discord ID.
    """

    m = comicdata.find_one({"name": "viewstats"})
    for member in members:
        m["members"][str(member)] = members[member]
    
    comicdata.replace_one({"name": "viewstats"}, m)


def get_date(field: str) -> date:
    """
    Gets the date given by the 'field' field in comicdata.viewstats.
    """

    update = comicdata.find_one({"name": "viewstats"})[field]
    return date(*map(int, update.split('-')))


def published(cnum: int) -> str:
    """
    Gets the publishing date of Comic #[cnum].
    """

    comic = comicdata.find_one({"nr": cnum})
    return comic["published"]
