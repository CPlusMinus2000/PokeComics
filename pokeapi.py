#!usr/bin/python3
# =====================================================================
# Module file that uses PokéPy (https://pokeapi.github.io/pokepy/)
#  to get Pokémon information (and hopefully more things later)
#  which can be displayed by the PokéComics bot
# =====================================================================

import pokepy as pk
import json
from typing import Union

ART = ("https://raw.githubusercontent.com/PokeAPI/sprites/"
        "master/sprites/pokemon/other/official-artwork/")

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
    
    else:
        if type(pokemon) == str:
            entry = json.load(open(f"pokedex/{pokemon.lower()}.json"))
            pokemon = int(entry["id"])
        
        return ART + f"{pokemon}.png"


if __name__ == "__main__":
    mew = pk.V2Client().get_pokemon("mew")
    print(mew.name)
