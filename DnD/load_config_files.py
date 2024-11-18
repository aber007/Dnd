import json
from os import path
from . import CONSTANTS

with open(path.join(path.dirname(__file__), CONSTANTS["item_config_file"]), "r") as f:
    file_contents = f.read()
ITEM_DATA : dict = json.loads(file_contents)

with open(path.join(path.dirname(__file__), CONSTANTS["enemy_config_file"]), "r") as f:
    file_contents = f.read()
ENEMY_DATA : dict = json.loads(file_contents)

with open(path.join(path.dirname(__file__), CONSTANTS["interaction_text_file"]), "r") as f:
    file_contents = f.read()
INTERACTION_DATA : dict = json.loads(file_contents)

with open(path.join(path.dirname(__file__), CONSTANTS["skill_tree_config_file"]), "r") as f:
    file_contents = f.read()
SKILL_TREE_DATA : dict = json.loads(file_contents)