import json
from os import path
from . import CONSTANTS

with open(path.join(path.dirname(__file__), CONSTANTS["item_config_file"]), "r") as f:
    file_contents = f.read()
ITEM_DATA = json.loads(file_contents)

with open(path.join(path.dirname(__file__), CONSTANTS["enemy_config_file"]), "r") as f:
    file_contents = f.read()
ENEMY_DATA = json.loads(file_contents)