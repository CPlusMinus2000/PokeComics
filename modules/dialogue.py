# YAML dialogue load

import yaml

with open("modules/dialogue.yml", 'r') as d:
    dialogue = yaml.safe_load(d)
