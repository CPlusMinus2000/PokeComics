
# Python module containing all the fun facts and things

words = {
    "lore": [],
    "references": [],
    "details": []
}

for key in words:
    with open(f"words/{key}.txt", 'r') as f:
        for line in f.readlines():
            words[key].append(line.strip())
