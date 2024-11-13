CONSTANTS = {
    "map_base_size": 9, #Base size over 20 is not recommended
    "room_probabilities": {
        "empty": 0.25,
        "enemy": 0.5,
        "chest": 0.2,
        "trap": 0.05,
        "mimic_trap": 0.05,
        "shop": 0.05
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
    "room_contains_text": {
        "empty": "nothing",
        "enemy": "an enemy",
        "chest": "a chest",
        "trap": "a trap",
        "mimic_trap": "a Mimic trap",
        "shop": "a shop"
    },

    "remove_door_percent": 0.3,

    "normal_trap_dmg": 3,
    "mimic_trap_ambush_dmg": 4,

    "player_inventory_size": 3,
    "player_hp": 10,
    "player_starting_gold": 0,
    
    "dice_sides": 20,
    "normal_trap_min_roll_to_escape": 10,
    "flee_min_roll_to_escape": 12,
    "flee_min_roll_to_escape_unharmed": 15,
    "flee_exact_roll_to_escape_coins": 20,
    
    "item_config_file": "./items.json",
    "enemy_config_file": "./enemies.json",
    "interaction_text_file": "./interaction_texts.json",

    "music": False,

    "directional_coord_offsets": {
        "N": [0, -1],
        "E": [1, 0],
        "S": [0, 1],
        "W": [-1, 0]
    },

    # change these when debugging
    "debug": {
        "gray_map_tiles": False, # default True
        "remove_room_doors": False, # default True
        "print_map": False # default False
    }
}

from .player_actions import get_user_action_choice
from .load_config_files import ITEM_DATA, ENEMY_DATA, INTERACTION_DATA
from .vector2 import Vector2
from .array2d import Array2D
from .items import Item, Inventory
from .main import run_game