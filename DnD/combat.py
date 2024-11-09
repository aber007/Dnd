import json
from os import path
from . import CONSTANTS

with open(path.join(path.dirname(__file__), CONSTANTS["enemies_config_file"]), "r") as f:
    file_contents = f.read()
items_data_dict = json.loads(file_contents)

class Combat:
    def __init__(self, player, enemy) -> None:
        self.player = player
        self.enemy = enemy
        self.turn = 0

    def start(self):
        while self.player.hp > 0 and self.enemy.hp > 0:
            self.turn += 1
            print(f"\n) Turn {self.turn} (")