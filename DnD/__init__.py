CONSTANTS = {
    "map_base_size": 9,
    "player_base_inventory_size": 3,
    "player_base_hp": 6,
    "enemy_base_hp": 4,
    "enemy_base_dmg": 2,
    "items_config_file": "./items.json"
}

from .items import Item, Inventory, items_data_dict
from .main import run_game