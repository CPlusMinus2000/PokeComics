# YAML emoji load

import yaml

with open("modules/emojis.yml", 'r') as d:
    emojis = yaml.safe_load(d)