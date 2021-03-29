
# ===============================================
# Downloads Pokédex data from Pokéapi.
# ===============================================

import urllib.request, urllib.error, json, os
import pokepy as pk
from typing import List

MAX_POKEMON = 898
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}


def scrape_dex(init: int = 1) -> None:
    i = init
    while i <= MAX_POKEMON:
        entry = f"https://pokeapi.co/api/v2/pokemon-species/{i}/"
        req = urllib.request.Request(url=entry, headers=headers)

        try:
            with urllib.request.urlopen(req) as url:
                data = json.loads(url.read().decode())
                json.dump(data, open(f"pokedex/{data['name']}.json", 'w'))
        
        except Exception as e:
            if e == urllib.error.HTTPError:
                print(i)
                continue
            
            elif e == urllib.error.URLError:
                continue
            
            else:
                raise
        
        i += 1


def build_index(folder: str = "pokedex", index: str = "index.json") -> None:
    """
    Builds an index for all of the Pokémon in the folder.
    """

    data = {}
    for filename in os.listdir(folder):
        if not filename.startswith("index") and filename.endswith(".json"):
            entry = json.load(open(f"{folder}/{filename}", 'r'))
            data[int(entry["id"])] = entry["name"]
    
    json.dump(data, open(index, 'w'), sort_keys=True)


def todict(obj, classkey=None):
    """
    Recursively convert an object (i.e. a Pokepy Pokemon) into a dictionary.
    """

    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.items() 
            if not callable(value) and not key.startswith('_')])
        
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        
        return data
    
    else:
        return obj


def pull_pokemon(folder: str = "pokeapi", init: int = 1) -> None:
    """
    Pulls files from the PokéApi database.
    Currently only pulls Pokémon data, but it should be easy to pull more.
    """

    i = init
    while i <= MAX_POKEMON:
        try:
            pok = pk.V2Client().get_pokemon(i)
            if isinstance(pok, list):
                pok = pok[0]
            
            f = f"{folder}/{pok.name}.json"
            json.dump(todict(pok), open(f, 'w'), sort_keys=True)
        
        except Exception as e:
            raise
            
        i += 1


def add_attributes(*attrs, init: int = 1) -> List[str]:
    """
    Adds attributes from files in pokeapi/ to files in pokedex/.
    """

    index = json.load(open("index.json", 'r'))
    special = []
    for i in range(init, MAX_POKEMON + 1):
        name = index[str(i)]
        try:
            dex_entry = json.load(open(f"pokedex/{name}.json", 'r'))
            api_entry = json.load(open(f"pokeapi/{name}.json", 'r'))

            for attr in attrs:
                dex_entry[attr] = api_entry[attr]
            
            json.dump(dex_entry, open(f"pokedex/{name}.json", 'w'), 
                        sort_keys=True)
        
        except FileNotFoundError:
            special.append(name)
    
    return special


if __name__ == "__main__":
    # scrape_dex(894)
    # build_index()
    # pull_pokemon(init=894)
    print(add_attributes("abilities", "height", "types", "weight"))
