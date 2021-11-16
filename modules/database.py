"""Database interface functions."""

from typing import Dict, Union, Optional, Iterable
from update import comicdata
from datetime import date
from modules.config import MEMBERS, VIEWSTATS, Member, Comic

def db_update(comic_num: int) -> None:
    """
    Updates the database, specifically any entry related to comic_num.
    """

    # Replace the comic
    curr = comicdata.find_one({"nr": comic_num})
    curr["viewed"] = True
    comicdata.replace_one({"nr": comic_num}, curr)

    viewstats = comicdata.find_one(VIEWSTATS)
    viewstats["lviewed"] = comic_num
    viewstats["updated"] = date.today().isoformat()

    # Update the latest viewstats
    comicdata.replace_one(VIEWSTATS, viewstats)


def get_comic(cnum: int, tag: str='c') -> Comic:
    """
    Gets the comic object for Comic #[cnum].
    """

    comic = comicdata.find_one({"nr": cnum, "tag": tag})
    return comic


def get_comics(
    cnum: Optional[int]=None, tag: Optional[str]=None
) -> Iterable[Dict[str, Comic]]:
    """
    Gets a cursor of comics matching the criteria from the database.
    """

    search = {}
    if cnum is not None:
        search["nr"] = cnum
    if tag is not None:
        search["tag"] = tag
    
    return comicdata.find(search)


def get_metadata(field: str) -> int:
    """
    Gets the specific viewstats metadata value indicated by 'field'.
    """

    return comicdata.find_one(VIEWSTATS)[field]


def get_members() -> Dict[Union[str, int], Member]:
    """
    Gets the members list from the database.
    """

    m = comicdata.find_one(MEMBERS)
    return m


# This is a dictionary of people in the server
people = comicdata.find_one(MEMBERS)
people = {
    int(key): value for key, value in people.items()
    if key.isdigit()
}

def set_metadata(field: str, value) -> None:
    """
    Sets the specific metadata value indicated by 'field'.
    """

    viewstats = comicdata.find_one(VIEWSTATS)
    viewstats[field] = value
    comicdata.replace_one(VIEWSTATS, viewstats)


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

    m = comicdata.find_one(MEMBERS)
    for member in members:
        m[str(member)] = members[member]
    
    comicdata.replace_one(MEMBERS, m)


def get_date(field: str) -> date:
    """
    Gets the date given by the 'field' field in comicdata.viewstats.
    """

    update = comicdata.find_one(VIEWSTATS)[field]
    return date(*map(int, update.split('-')))


def published(cnum: int) -> str:
    """
    Gets the publishing date of Comic #[cnum].
    """

    comic = comicdata.find_one({"nr": cnum})
    return comic["published"]
