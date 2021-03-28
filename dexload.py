
# ===============================================
# Downloads Pokédex data from Pokéapi.
# ===============================================

import urllib.request, urllib.error, json, os

MAX_POKEMON = 893
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
        
        i += 1


def build_index(folder: str = "pokedex", index: str = "index.json") -> None:
    """
    Builds an index for all of the Pokémon in the folder.
    """

    data = {}
    for filename in os.listdir(folder):
        if not filename.startswith("index") and filename.endswith(".json"):
            entry = json.load(open(filename, 'r'))
            data[int(entry["id"])] = entry["name"]
    
    json.dump(data, open(index, 'w'))


if __name__ == "__main__":
    build_index()
