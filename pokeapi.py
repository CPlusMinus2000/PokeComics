#!usr/bin/python3
# =====================================================================
# Module file that uses PokéPy (https://pokeapi.github.io/pokepy/)
#  to get Pokémon information (and hopefully more things later)
#  which can be displayed by the PokéComics bot
# =====================================================================

import pokepy as pk
import json, yaml
from typing import Union, List

ART = ("https://raw.githubusercontent.com/PokeAPI/sprites/"
        "master/sprites/pokemon/other/official-artwork/")

ABILITY = "https://bulbapedia.bulbagarden.net/wiki/%s_(Ability)"
LINK = "https://student.cs.uwaterloo.ca/~cqhe/types/%s.png"


# some important information
index = json.load(open("index.json", 'r'))
types = yaml.safe_load(open("types/types.yml", 'r'))

class Pokemon:
    """
    A class to represent a Pokémon, for use in Pokédex entries.
    """

    def __init__(self, pokemon: Union[str, int]) -> None:
        if isinstance(pokemon, int):
            pokemon = index[str(pokemon)]
        
        self.name = pokemon
        self.attrs = json.load(open(f"pokedex/{pokemon}.json", 'r'))
        self.id = int(self.attrs["id"])
    
    def __repr__(self) -> str:
        return f"{self.id} - {self.name}"
    
    def __contains__(self, item: str) -> bool:
        return item in self.attrs

    #TODO: Add addition (True if and only if Pokémon are birth compatible)
        
    def get_sprite(self, use_api: bool = False) -> str:
        """
        Gets an image link to the official artwork sprite of
        the Pokémon with name or ID `pokemon`.
        """

        if use_api:
            info = pk.V2Client().get_pokemon(self.name)
            if type(info) == list:
                info = info[0]
            
            return ART + f"{info.id}.png"
        
        else: # Use locally stored files to access IDs          
            return ART + f"{self.id}.png"


    def get_types(self, link: bool = False) -> List[str]:
        """
        Returns a list of the types of the input Pokémon.
        """

        typ = []
        for type in self.attrs["types"]:
            # typ.append(types[type["type"]["name"]])
            if link:
                typ.append(LINK % type["type"]["name"])
            else:
                typ.append(type["type"]["name"])

        return typ


    def get_abilities(self) -> List[str]:
        """
        Gets a list of the abilities of the input Pokémon, 
        formatted to have markdown-embedded Bulbapedia links
        (and also spoiler tags over hidden abilities).
        """

        abilities = []
        for a in self.attrs["abilities"]:
            name = a["ability"]["name"]
            link = ABILITY % name.capitalize()
            message = f"[{name.capitalize()}]({link})"

            if a["is_hidden"]: # Put spoiler tags over the link
                message = f"||{message}||"
            
            abilities.append(message)
        
        return abilities


    def get_genus(self) -> str:
        """
        Gets the genus of a Pokémon.
        """

        for genus in self.attrs["genera"]:
            if genus["language"]["name"] == "en": # English
                return genus["genus"]
        
        return "ERROR: GENUS NOT FOUND"

if __name__ == "__main__":
    mew = pk.V2Client().get_pokemon("mew")
    print(mew.name)
