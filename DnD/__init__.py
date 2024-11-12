CONSTANTS = {
    "map_base_size": 9, #Base size over 20 is not recommended
    "room_probabilities": {
        "empty": 0.25,
        "enemy": 0.4,
        "chest": 0.25,
        "trap": 0.05,
        "mimic_trap": 0.05,
        "shop": 0.1
    },
    "room_ui_colors": {
        "default" : "gray",
        "discovered": "light gray",
        "empty": "light gray",
        "enemy": "red",
        "chest": "yellow",
        "trap": "dark green",
        "mimic_trap": "light green",
        "shop": "blue",
    },

    "normal_trap_base_dmg": 3,

    "player_base_inventory_size": 3,
    "player_base_hp": 1000000,
    "player_starting_gold": 0,
    "player_base_defence" : 0,
    
    "enemy_base_hp": 4,
    "enemy_base_dmg": 2,
    "enemy_special" : "none",
    "enemy_special_info": "none",
    "enemy_defence_melee": 0,
    "enemy_defence_ranged": 0,
    "enemy_defence_magic": 0,
    "enemy_exp": 1,
    "enemy_gold": 1,
    
    "dice_base_sides": 20,
    'normal_trap_base_min_roll_to_escape': 10,
    "mimic_trap_base_ambush_dmg": 4,
    
    "item_config_file": "./items.json",
    "enemy_config_file": "./enemies.json",
    "interaction_text_file": "./interaction_texts.json",

    "music": True
}

from .player_actions import get_user_action_choice
from .load_config_files import ITEM_DATA, ENEMY_DATA, INTERACTION_DATA
from .vector2 import Vector2
from .items import Item, Inventory
from .main import run_game