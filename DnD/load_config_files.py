import json
from os import path
from . import CONSTANTS

cwd = path.dirname(__file__)

with open(path.join(cwd, CONSTANTS["item_config_file"]), "r") as f:
    file_contents = f.read()
ITEM_DATA : dict = json.loads(file_contents)

with open(path.join(cwd, CONSTANTS["enemy_config_file"]), "r") as f:
    file_contents = f.read()
ENEMY_DATA : dict = json.loads(file_contents)

with open(path.join(cwd, CONSTANTS["interaction_text_file"]), "r") as f:
    file_contents = f.read()
INTERACTION_DATA : dict = json.loads(file_contents)

with open(path.join(cwd, CONSTANTS["skill_tree_config_file"]), "r") as f:
    file_contents = f.read()
SKILL_TREE_DATA : dict = json.loads(file_contents)

with open(path.join(cwd, CONSTANTS["rooms_config_file"]), "r") as f:
    file_contents = f.read()
ROOM_DATA : dict = json.loads(file_contents)