#!usr/bin/python3
# =====================================================================
# Module file that uses PokéPy (https://pokeapi.github.io/pokepy/)
#  to get Pokémon information (and hopefully more things later)
#  which can be displayed by the PokéComics bot
# =====================================================================

import pokepy as pk
import json
from typing import Union, List

ART = ("https://raw.githubusercontent.com/PokeAPI/sprites/"
        "master/sprites/pokemon/other/official-artwork/")

ABILITY = "https://bulbapedia.bulbagarden.net/wiki/%s_(Ability)"

def get_sprite(pokemon: Union[str, int], use_api: bool = False) -> str:
    """
    Gets an image link to the official artwork sprite of
    the Pokémon with name or ID `pokemon`.
    """

    if use_api:
        info = pk.V2Client().get_pokemon(pokemon)
        if type(info) == list:
            info = info[0]
        
        return ART + f"{info.id}.png"
    
    else: # Use locally stored files to access IDs
        if type(pokemon) == str:
            entry = json.load(open(f"pokedex/{pokemon.lower()}.json"))
            pokemon = int(entry["id"])
        
        return ART + f"{pokemon}.png"


def get_attrs(pokemon: Union[str, int], attribute: str):
    """
    Returns attributes of the input Pokémon.
    """

    if isinstance(pokemon, int):
        index = json.load(open("index.json", 'r'))
        pokemon = index[str(pokemon)]
    
    dex = json.load(open(f"pokedex/{pokemon}.json", 'r'))
    return dex[attribute]


def get_types(pokemon: Union[str, int]) -> List[str]:
    """
    Returns a list of the types of the input Pokémon.
    """

    return [t["type"]["name"] for t in get_attrs(pokemon, "types")]


def get_abilities(pokemon: Union[str, int]) -> List[str]:
    """
    Gets a list of the abilities of the input Pokémon, 
    formatted to have markdown-embedded Bulbapedia links
    (and also spoiler tags over hidden abilities).
    """

    abilities = []
    for a in get_attrs(pokemon, "abilities"):
        name = a["ability"]["name"]
        link = ABILITY % name.capitalize()
        message = f"[{name.capitalize()}]({link})"

        if a["is_hidden"]: # Put spoiler tags over the link
            message = f"||{message}||"
        
        abilities.append(message)
    
    return abilities


def get_genus(pokemon: Union[str, int]) -> str:
    """
    Gets the genus of a Pokémon.
    """

    for genus in get_attrs(pokemon, "genera"):
        if genus["language"]["name"] == "en": # English
            return genus["genus"]
    
    return "ERROR: GENUS NOT FOUND"

if __name__ == "__main__":
    mew = pk.V2Client().get_pokemon("mew")
    print(mew.name)
