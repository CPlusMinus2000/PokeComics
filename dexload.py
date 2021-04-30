
# ===============================================
# Downloads Pokédex data from PokéApi.
# ===============================================

import urllib.request, urllib.error, json, yaml, os
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
                data["characters"] = []
                json.dump(data, open(f"pokedex/{data['name']}.json", 'w'),
                            indent=4, sort_keys=True)
        
        except urllib.error.HTTPError:
            print(i)
            continue
            
        except urllib.error.URLError:
            continue
        
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
    
    with open(index, 'w') as ind_file:
        json.dump(data, open(ind_file, 'w'), indent=4, sort_keys=True)


def todict(obj, classkey=None):
    """
    Recursively convert an object (i.e. a Poképy Pokémon) into a dictionary.
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
    with open("index.yml", 'r') as ifile:
        index = yaml.safe_load(ifile)
    
    with open("forms.json", 'r') as ffile:
        forms = json.load(ffile)
    
    while i <= MAX_POKEMON:
        pok = pk.V2Client().get_pokemon(i)            
        if pok.name.split('-')[0] in forms:
            poks = forms[pok.name.split('-')[0]]
            for p in poks:
                pok = pk.V2Client().get_pokemon(p)
                with open(f"{folder}/{pok.name}.json", 'w') as f:
                    json.dump(todict(pok), f, indent=4, sort_keys=True)
        
        else:
            with open(f"{folder}/{pok.name}.json", 'w') as f:
                json.dump(todict(pok), f, indent=4, sort_keys=True)
            
        i += 1


def add_attributes(init: int = 1, *attrs) -> List[str]:
    """
    Adds attributes from files in pokeapi/ to files in pokedex/.
    """

    with open("index.yml", 'r') as ind:
        index = yaml.safe_load(ind)
    
    with open("forms.json", 'r') as ffile:
        forms = json.load(ffile)
    
    for i in range(init, MAX_POKEMON + 1):
        name = index[i]
        with open(f"pokedex/{name}.json", 'r') as f:   
            dex_entry = json.load(f)

        if name in forms:
            for attr in attrs:
                values = {}
                for form in forms[name]:
                    with open(f"pokeapi/{form}.json", 'r') as g:
                        api_entry = json.load(g)
                    
                    values[form] = api_entry[attr]
                
                dex_entry[attr] = values

        else:
            with open(f"pokeapi/{name}.json", 'r') as g:
                api_entry = json.load(g)

            for attr in attrs:
                dex_entry[attr] = api_entry[attr]
        
        with open(f"pokedex/{name}.json", 'w') as f:
            json.dump(dex_entry, f, indent=4, sort_keys=True)
    
    return attrs


if __name__ == "__main__":
    # scrape_dex(894)
    # build_index()
    # pull_pokemon(init=740)
    print(add_attributes(1, "abilities", "height", "types", "weight"))
