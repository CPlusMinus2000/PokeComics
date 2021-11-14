# I'll put schema modifications in here, just collecting them really

from update import update_members_schema, Member
from typing import List, Dict, Any
from modules.config import RPHONE_TOPICS, RPHONE_DEFAULT_LENGTH


def add_field(member: Member, key: str, value: Any) -> None:
    """
    Adds a field to each member with a given key and value.
    """

    member[key] = value


def add_rphone(member: Member) -> None:
    """
    Adds rphone topics to each member.
    """

    add_field(
        member, "rphone", {
            t: [False] * RPHONE_DEFAULT_LENGTH 
            for t in RPHONE_TOPICS if t != "main"
        }
    )


def add_pity(member: Member) -> None:
    """
    Adds pity timers to each member.
    """

    add_field(member, "pity", 0)


if __name__ == "__main__":
    update_members_schema(add_pity)
