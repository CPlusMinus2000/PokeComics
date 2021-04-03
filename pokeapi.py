#!usr/bin/python3
# =====================================================================
# Module file that uses PokéPy (https://pokeapi.github.io/pokepy/)
#  to get Pokémon information (and hopefully more things later)
#  which can be displayed by the PokéComics bot
# =====================================================================

import pokepy as pk
import json, yaml, random
from typing import Union, List

ART = ("https://raw.githubusercontent.com/PokeAPI/sprites/"
        "master/sprites/pokemon/other/official-artwork/")

ABILITY = "https://bulbapedia.bulbagarden.net/wiki/%s_(Ability)"
LINK = "https://student.cs.uwaterloo.ca/~cqhe/types/%s.png"


# some important information
index = json.load(open("index.json", 'r'))
types = yaml.safe_load(open("types/types.yml", 'r'))


def special_cases(pokemon: str) -> str:
    """
    A function for handling Pokémon whose names are a bit more finicky.
    """

    poke = pokemon.lower()
    if "mr" in poke and "mime" in poke:
        return "mr-mime"
    elif "mr" in poke and "rime" in poke:
        return "mr-rime"
    elif "mime" in poke and "jr" in poke:
        return "mime-jr"
    elif "type" in poke and "null" in poke:
        return "type-null"
    elif "tapu" in poke and "bulu" in poke:
        return "tapu-bulu"
    elif "tapu" in poke and "fini" in poke:
        return "tapu-fini"
    elif "tapu" in poke and "koko" in poke:
        return "tapu-koko"
    elif "tapu" in poke and "lele" in poke:
        return "tapu-lele"
    elif "nidoran" in poke and 'f' in poke:
        return "nidoran-f"
    elif "nidoran" in poke and 'm' in poke:
        return "nidoran-m"
    elif "nidoran" in poke:
        return "nidoran" + random.sample(['f', 'm'], 1)[0]
    
    return pokemon

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
        self.capture = int(self.attrs["capture_rate"])
        self.happiness = int(self.attrs["base_happiness"])
        self.colour = self.attrs["color"]["name"]
        self.height = int(self.attrs["height"])
        self.weight = int(self.attrs["weight"])
        self.characters = self.attrs.get("characters")

        if self.characters is None:
            self.characters = ["N/A"]
    
    def __repr__(self) -> str:
        return f"{self.id} - {self.name}"
    
    def __contains__(self, item: str) -> bool:
        return item in self.attrs

    #TODO: Add addition (True if and only if Pokémon are birth compatible)

    def punctuate(self) -> str:
        """
        Returns the name of the Pokémon in a correctly-punctuated string.
        """

        # For most Pokémon, this won't do anything.
        # However, there are some special cases.
        if self.name == "mr-mime":
            return "Mr. Mime"
        elif self.name == "mr-rime":
            return "Mr. Rime"
        elif self.name == "mime-jr":
            return "Mime Jr."
        elif self.name == "type-null":
            return "Type: Null"
        elif "tapu" in self.name:
            return self.name.replace('-', ' ').title()
        elif "nidoran" in self.name:
            return f"Nidoran ({self.name[-1].upper()})"
        
        return self.name.title()
        
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


    def get_genus(self, language: str = "en") -> str:
        """
        Gets the genus of a Pokémon.

        If language is specified, that will be the chosen one; 
        otherwise English will be used.
        """

        for genus in self.attrs["genera"]:
            if genus["language"]["name"] == language:
                return genus["genus"]
        
        return "ERROR: GENUS NOT FOUND"
    
    def get_flavour(self, language: str = "en", version = None) -> str:
        """
        Gets the flavour text of a Pokémon.

        If language is specified, that language will be searched for; 
        otherwise English will be used.

        If version is specified, that version's text will be search for;
        otherwise, a random entry will be used.
        """

        entries = []
        for flavour in self.attrs["flavor_text_entries"]:
            if flavour["language"]["name"] == language:
                if version is None:
                    entries.append(flavour["flavor_text"].replace('\n', ' '))
                elif flavour["version"]["name"] == version:
                    return flavour["flavor_text"].replace('\n', ' ')
        
        if version is not None and language != "en" and not entries:
            return "I can't find an entry with that language or version."
        elif version is not None and not entries:
            return "I can't find an entry with that version name. :("
        elif not entries and language != "en":
            return "Sorry, I can't find any entries with that language."
        elif not entries:
            return "Weird... I can't find any entries."
        else:
            return random.sample(entries, 1)[0]
    
    def get_size(self) -> str:
        """
        Gets a string representing height and weight (in metric).
        """

        return f"{self.height / 10}m/{self.weight / 10}kg"
    
    def format_gender(self) -> str:
        """
        Returns a string representing gender ratio.
        """

        ratio = self.attrs["gender_rate"]
        if ratio == -1:
            return "Genderless"
        else:
            male, female = "\N{MALE SIGN}", "\N{FEMALE SIGN}"
            return f"{(8 - ratio) / 0.08}% {male}/{ratio / 0.08}% {female}"


if __name__ == "__main__":
    mew = pk.V2Client().get_pokemon("mew")
    print(mew.name)
