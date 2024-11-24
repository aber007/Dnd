CONSTANTS = {
    "map_base_size": 10, #Base size over 20 is not recommended
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
    "room_contains_text": {
        "empty": "nothing",
        "enemy": "an enemy",
        "chest": "a chest",
        "trap": "a trap",
        "mimic_trap": "a Mimic trap",
        "shop": "a shop"
    },

    "remove_door_percent": 0.2,

    "normal_trap_dmg": 3,
    "mimic_trap_ambush_dmg": 4,

    "player_inventory_size": 4,
    "player_hp": 50,
    "player_max_hp": 50,
    "player_base_defence" : 0,
    "player_starting_gold": 0,
    "player_starting_exp": 0,
    "player_starting_lvl": 0,
    "player_default_temp_dmg_factor": 1,
    
    "player_exp_to_lvl_func": lambda exp: int(exp**0.5),
    "player_lvl_to_exp_func": lambda lvl: int(lvl**2),
    "player_lvl_to_bonus_hp_additive_func": lambda lvl: lvl,
    "player_lvl_to_bonus_dmg_additive_func": lambda lvl: lvl,
    
    "player_movement_anim_duration": 0.2,
    "player_movement_anim_active_update_delay": 5,
    
    "dice_sides": 20,
    "normal_trap_min_roll_to_escape": 10,
    "flee_min_roll_to_escape": 12,
    "flee_min_roll_to_escape_unharmed": 15,
    "flee_exact_roll_to_escape_coins": 20,
    "flee_20_coins_to_receive_divider": 2,
    
    "shop_item_count": 3,
    "shop_item_price_range_divider": 2,

    "item_config_file": "./items.json",
    "enemy_config_file": "./enemies.json",
    "interaction_text_file": "./interaction_texts.json",
    "skill_tree_config_file": "./skill_tree.json",
    "encrypted_lore_file": "./story/lore_text/encrypted_pages.json",
    "discovered_pages_file": "./story/lore_text/discovered_pages.json",

    "music_enabled": True,
    "music_max_volume_percent": 0.75,
    "music_slider_step_volume_percent": 0.015,

    "directional_coord_offsets": {
        "N": [0, -1],
        "E": [1, 0],
        "S": [0, 1],
        "W": [-1, 0]
    },
    "player_movement_anim_duration": 0.2,
    "player_movement_anim_active_update_delay": 5,

    "hp_bar_max_length": 50,
    "hp_bar_fill_color": [242,13,13],
    "exp_bar_max_length": 50,
    "exp_bar_fill_color": [48, 219, 0],

    "dodge_bar_length": 30,
    "dodge_bar_colors": {
        "red": [255, 0, 0],
        "orange": [255, 165, 0],
        "green": [0, 255, 0]
    },
    "dodge_bar_times": {
        "waiting": 3000,
        "waiting_range": 1500,
        "perfect_dodge": 240,
        "partial_dodge": 550
    },
    "dodge_bar_dmg_factors": {
        "red": 1,
        "orange": 0.5,
        "green": 0
    },

    "skill_tree_check_color": [0,255,0],
    "skill_tree_cross_color": [255,0,0],

    "use_fancy_item_selection": True,
    "min_desired_terminal_width": 110,

    "header_length": 39,

    # change these when debugging
    "debug": {
        "set_all_map_tiles_discovered": False, # default False
        "display_all_walls": False, # default False
        "print_map": False, # default False
        "player_infinite_dmg": False, # default False
        "show_enemy_probabilities" : False # default False
    }
}

from .load_config_files import ITEM_DATA, ENEMY_DATA, INTERACTION_DATA, SKILL_TREE_DATA
from .ANSI import ANSI
from .console_io import Console
from .player_inputs import PlayerInputs
from .terminal import ensure_terminal_width, wait_for_key, ItemSelect, Slider, combat_bar, Bar, ANSI, DodgeEnemyAttack
from .ambience import Music
from .logging import Log
from .lore import Lore
from .player_actions import get_user_action_choice
from .main_menu import MainMenu
from .animation import AnimationLibrary, Animation
from .vector2 import Vector2
from .array2d import Array2D
from .UI_map_creation import openUIMap
from .items import Item, Inventory
from .effects import Effect
from .create_walls_algorithm import CreateWallsAlgorithm
from .main import run_game
