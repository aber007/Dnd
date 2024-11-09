CONSTANTS = {
    "map_base_size": 9,
    "trap_base_dmg": 3,

    "player_base_inventory_size": 3,
    "player_base_hp": 10,
    
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
    "enemy_config_file": "./enemies.json"
}

from .load_config_files import ITEM_DATA, ENEMY_DATA
from .items import Item, Inventory
from .main import run_game