import os
from random import randint, choices, choice, uniform
from time import sleep
from .UI_map_creation import openUIMap
from .ambience import Music
from . import (
    CONSTANTS,
    ITEM_DATA,
    ENEMY_DATA,
    INTERACTION_DATA,
    Item,
    Inventory,
    Vector2,
    get_user_action_choice
    )

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager



class Entity:
    def take_damage(self, dmg : int) -> int:
        caller = type(self).__name__
        if isinstance(self, Enemy):
            dmg -= max(0, self.defence_melee)
        elif isinstance(self, Player):
            dmg -= max(0, self.defence)
        self.hp = max(0, self.hp - dmg)
        self.is_alive = 0 < self.hp
        
        return dmg

class Player(Entity):
    def __init__(self, parent_map) -> None:
        self.parent_map : Map = parent_map
        self.position : Vector2 = self.parent_map.starting_position
        self.hp = CONSTANTS["player_hp"]
        self.is_alive = True
        self.gold = CONSTANTS["player_starting_gold"]
        self.active_dice_effects : list[int] = []
        self.defence = CONSTANTS["player_base_defence"]
        
        self.inventory = Inventory()

        self.current_combat : Combat | None = None
    
    def get_dice_modifier(self) -> int:
        return sum(self.active_dice_effects)
    
    def roll_dice(self) -> tuple[bool,int] | int:
        """Roll the dice and include any dice modifiers. Return the result"""

        # get a random number between 1 and dice_sides then add the dice modifier
        # max() ensures the roll has a min value of 1
        dice_result = max(1, randint(1, CONSTANTS["dice_sides"]) + self.get_dice_modifier())
        self.active_dice_effects.clear()

        return dice_result

    def open_inventory(self) -> tuple[int, str] | None:
        """If any damage was dealt, return the amount and item name_in_sentence.\n
        If no damage was dealt return None"""

        selected_item : Item | None = self.inventory.open()
        #for later   if player.in_shop: return selected_item

        if selected_item == None:
            return None

        if selected_item.offensive:
            if self.current_combat == None:
                print("\nYou shouldn't use an offensive item outside of combat")
            else:
                dmg = selected_item.use()
                return (dmg, selected_item.name_in_sentence)

        else:
            # non offensive items always return a callable where the argument 'player' is expected
            use_callable = selected_item.use()
            use_callable(self)

    def heal(self, additional_hp : int):
        # cap the hp to player_hp
        hp_before = self.hp
        self.hp = min(self.hp + additional_hp, CONSTANTS["player_hp"])
        print(f"The player was healed for {additional_hp}. HP: {hp_before} -> {self.hp}")

    def attack(self, target, item) -> int:
        """Attack target your weapons damage dmg_multiplier. The damage dealt is returned"""
        print(target)
        dmg = self.inventory.equipped_weapon.use() 
        target.take_damage(dmg)
        return dmg

class Enemy(Entity):
    def __init__(self, enemy_type : str, target : Player) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value won't be useful it's not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.is_alive = True
    
    def attack(self, target, dmg_multiplier : int = 1) -> int:
        """Attack target with base damage * dmg_multiplier. The damage dealt is returned"""
        return target.take_damage(self.dmg * dmg_multiplier)
    
    def use_special(self, special : str) -> None:
        """Runs the code for special abilities which can be used during combat"""
        pass


class Map:
    class Room:

        def __init__(self, type, discovered, doors, parent_map) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.chest_item : Item | None = None
            self.is_cleared : bool = False

        def on_enter(self, player : Player, map, first_time_entering_room : bool, music : Music) -> None:
            """Called right when the player enters the room. E.g. starts the trap interaction or decides a chest's item etc"""

            # the enemy spawn, chest_item decision and shop decisions should only happen once
            # the non-mimic trap should always trigger its dialog
            match (self.type, first_time_entering_room):
                case ("enemy", _):
                    if not map.get_room(player.position).is_cleared:
                        Combat(player, map).start(music=music)

                case ("chest", True):
                    possible_items = list(ITEM_DATA.keys())
                    item_probabilites = [ITEM_DATA[item_id]["probability"] for item_id in possible_items]
                    chosen_chest_item_id = choices(possible_items, item_probabilites)[0]
                    self.chest_item = Item(chosen_chest_item_id)
                    print(choice(INTERACTION_DATA["chest"]))

                case ("shop", True):
                    music.stop()
                    music.play("shop")
                    pass # decide shop's wares/prices?

                case ("trap", _):
                    print(f"\nYou stepped in a trap! Roll at least {CONSTANTS['normal_trap_min_roll_to_escape']} to save yourself")
                    prompt_dice_roll()
                    roll = player.roll_dice()

                    if CONSTANTS["normal_trap_min_roll_to_escape"] <= roll:
                        print(f"You rolled {roll} and managed to escape unharmed")
                    else:
                        print(f"You rolled {roll} and was harmed by the trap while escaping")
                        dmg_taken = player.take_damage(CONSTANTS["normal_trap_dmg"])
                        print(f"The player took {dmg_taken} damage. {player.hp} HP remaining")
                    self.is_cleared = True
            
            # update the tile the player just entered
            player.parent_map.UI_instance.send_command("tile", player.position, player.parent_map.decide_room_color(player.position))

        def interact(self, player : Player, map, music : Music) -> None:
            """Called when the player chooses to interact with a room. E.g. opening a chest or opening a shop etc\n
            This is especially useful when dealing with the mimic trap as appears to be a chest room, thus tricking the player into interacting"""

            match self.type:
                case "chest":
                    player.inventory.receive_item(self.chest_item)
                    self.chest_item = None
                    self.is_cleared = True

                case "mimic_trap":
                    print(choice(INTERACTION_DATA["mimic"]))
                    dmg_taken = player.take_damage(CONSTANTS["mimic_trap_ambush_dmg"])
                    print(f"The player took {dmg_taken} damage from the Mimic ambush. {player.hp} HP remaining", end="\n"*2)
                    Combat(player, map, force_enemy_type = "Mimic").start(music=music)

                case "shop":
                    pass # shop dialog
            
            # update the tile the player just interacted with
            player.parent_map.UI_instance.send_command("tile", player.position, player.parent_map.decide_room_color(player.position))

    class UI:
        def __init__(self, size, rooms) -> None:
            # to be set by the parent Map object
            self.size : int = size
            self.rooms : list[list[Map.Room]] = rooms

            self.manager = Manager()
            self.command_queue = self.manager.Queue(100)
            self.UI_thread : Process | None = None
        
        def open(self, player_pos : Vector2):
            self.UI_thread = Process(target=openUIMap, args=(self.size, self.rooms, player_pos, self.command_queue))
            self.UI_thread.start()
            sleep(0.5)
        
        def send_command(self, type : str, position : Vector2, *args : str):
            """Type is ether "pp" (player position) to move player position rect or "tile" to change bg color of a tile\n
            Eg. send_command("pp", player.position) updates the player rect postion to the players current position\n
            Eg. send_command("tile", player.position + Vector2(0,1), "blue") sets background color of the tile to the players north to blue"""
            command_line = f"{type} {position.x},{position.y}"
            if len(args):
                command_line += " " + " ".join([str(arg) for arg in args])
            self.command_queue.put_nowait(command_line)
        
        def close(self):
            self.UI_thread.terminate()
            self.UI_thread.join()
            self.UI_thread.close()

    def __init__(self, size : int = CONSTANTS["map_base_size"]) -> None:
        """Generates the playable map"""
        self.size = size

        if self.size % 2 == 0:
            self.size += 1
        self.starting_position = Vector2(double=int(self.size/2))
        room_types = list(CONSTANTS["room_probabilities"].keys())
        probabilities = list(CONSTANTS["room_probabilities"].values())
        # Initialize 2D array
        rooms = [[0 for x in range(self.size)] for y in range(self.size)]
        

        # Assign random values to each location with set probabilities
        for x in range(self.size):
            for y in range(self.size):
                if x == int(self.size/2) and y == int(self.size/2):
                    rooms[x][y] = Map.Room(type="empty", discovered=True, doors=["N", "E", "S", "W"], parent_map=self)
                else:
                    roomtype = choices(room_types, probabilities)[0]
                    rooms[x][y] = Map.Room(type=roomtype, discovered=False, doors=["N", "E", "S", "W"], parent_map=self)
        self.rooms : list[list[Map.Room]] = rooms

        self.UI_instance = Map.UI(self.size, self.rooms)
    
    def open_UI_window(self, player_pos : Vector2) -> None:
        """Opens the playable map in a separate window"""

        # Press the map and then escape to close the window
        self.UI_instance.open(player_pos)
    
    def close_UI_window(self) -> None:
        self.UI_instance.close()

    def get_room(self, position : Vector2) -> Room:
        """Using an x and a y value, return a room at that position"""
        return self.rooms[position.x][position.y]
    
    def decide_room_color(self, room_position : Vector2) -> str:
        room : Map.Room = self.rooms[room_position.x][room_position.y]
        colors = CONSTANTS["room_ui_colors"]

        match room.type:
            case "empty":
                return colors["discovered"] if room.discovered else colors["empty"]

            case "enemy":
                return colors["discovered"] if room.is_cleared else colors["enemy"]

            case "chest":
                return colors["discovered"] if room.is_cleared else colors["chest"]

            case "trap":
                return colors["trap"]

            case "mimic_trap":
                return colors["discovered"] if room.is_cleared else colors["mimic_trap"]

            case "shop":
                return colors["shop"]



    def move_player(self, direction : str, player : Player, music : Music) -> None:
        """Move the player in the given direction"""
        x, y = player.position
    
        match direction:
            case "N":
                if y > 0:  # Ensure not moving out of bounds
                    y -= 1
            case "S":
                if y < len(self.rooms) - 1:  # Ensure not moving out of bounds
                    y += 1
            case "E":
                if x < len(self.rooms[0]) - 1:  # Ensure not moving out of bounds
                    x += 1
            case "W":
                if x > 0:  # Ensure not moving out of bounds
                    x -= 1

        player.position = Vector2(x, y)

        first_time_entering_room = not self.rooms[x][y].discovered
        self.rooms[x][y].discovered = True
        
        self.UI_instance.send_command("tile", player.position, self.decide_room_color(player.position))
        self.UI_instance.send_command("pp", player.position)

        self.rooms[x][y].on_enter(player = player, map = self, first_time_entering_room = first_time_entering_room, music=music)


class Combat:
    def __init__(self, player : Player, map : Map, force_enemy_type : str | None = None) -> None:
        self.player : Player = player
        self.map : Map = map
        self.enemy : Enemy = self.create_enemy(force_enemy_type)
        self.turn = 0

    def create_enemy(self, force_enemy_type : str | None) -> Enemy:
        """Decide enemy type to spawn, then return enemy object with the attributes of said enemy type"""

        # needed for mimic traps
        if force_enemy_type:
            return Enemy(enemy_type = force_enemy_type, target = self.player)


        enemy_types = list(ENEMY_DATA.keys())

        spawn_probabilities : dict[str, float | int] = {}
        for enemy_type in enemy_types:
            # if an enemy's probability is -1 it should only be spawned using force_enemy_type
            if (enemy_probability := ENEMY_DATA[enemy_type]["probability"]) != -1:
                spawn_probabilities[enemy_type] = enemy_probability

        distace_from_spawn = ((abs(self.map.starting_position.x - self.player.position.x)**2) + (abs(self.map.starting_position.y - self.player.position.y)**2))**0.5
        # """Adjust probabilites depending on distance away from spawn and difficulty of enemy""" Should be changed later
        for enemy_type in enemy_types:
            if ENEMY_DATA[enemy_type]["probability"] == 0:
                new_probability = distace_from_spawn * ((100-ENEMY_DATA[enemy_type]["exp"])/1000)
                spawn_probabilities[enemy_type] += new_probability

        enemy_type_to_spawn = choices(list(spawn_probabilities.keys()), list(spawn_probabilities.values()))[0]

        return Enemy(enemy_type = enemy_type_to_spawn, target = self.player)

    def start(self, music : Music):
        # remember to deal with Enemy.on_damage_taken, Enemy.on_death, Player.on_damage_taken, Player.on_death
        music.fadeout()
        music.play(type="fight")
        print(f"{'='*15} Combat {'='*15}")
        story_text_enemy = str(choice(INTERACTION_DATA["enemy"]))
        if "enemy" in story_text_enemy:
            story_text_enemy.replace("enemy", self.enemy.name_in_sentence)
            print(story_text_enemy.replace("enemy", self.enemy.name_in_sentence))
        else:
            print(story_text_enemy)
            print(f"\nAn enemy appeared! It's {self.enemy.name_in_sentence}!")
        enemyturn = choice([True, False])

        self.player.current_combat = self

        while self.player.is_alive and self.enemy.is_alive:
            self.turn += 1

            print(f"\n) Turn {self.turn} (")
            print(f"Player hp: {self.player.hp}")
            print(f"{self.enemy.name} hp: {self.enemy.hp} \n")

            if not enemyturn:
                action_completed = False  # Loop control variable to retry actions
                while not action_completed:
                    action_options = ["Use item / Attack", "Attempt to Flee"]
                    action_idx = get_user_action_choice("Choose action: ", action_options)

                    match action_options[action_idx]:                   
                        case "Use item / Attack":
                            # item_return is either tuple[dmg done, item name_in_sentence] or None, depending on if any damage was done
                            item_return = self.player.open_inventory()
                            if item_return is not None:
                                print(item_return)
                                dmg, item_name_in_sentence = item_return
                                dmg_dealt = self.enemy.take_damage(dmg)
                                print(f"The {self.enemy.name} was hurt by the player using {item_name_in_sentence}")
                                print(f"\nYou attacked the {self.enemy.name} for {dmg_dealt} damage")
                                action_completed = True  
                            else:
                                continue 

                        case "Attempt to Flee":
                            print("Attempting to flee, Roll 12 or higher to succeed")
                            prompt_dice_roll()
                            roll = self.player.roll_dice()
                            print(f"You rolled {roll}")

                            # if you managed to escape
                            if 12 <= roll:
                                # if the enemy hit you on your way out
                                if roll < 15:
                                    dmg_dealt_to_player = self.enemy.attack(target=self.player)
                                    if self.player.is_alive:
                                        print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing\nPlayer hp remaining: {self.player.hp}")
                                    else:
                                        print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing, killing you in the process")
                                        self.enemy.is_alive = False
                                
                                # if you escaped with coins
                                elif roll == 20:
                                    print(choice(INTERACTION_DATA["escape_20"]))
                                    self.player.gold += self.enemy.gold // 2
                                print(choice(INTERACTION_DATA["escape"]))
                                self.enemy.is_alive = False

                            # if you didnt escape
                            else:
                                dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=2)
                                if self.player.is_alive:
                                    print(f"You failed to flee and took {dmg_dealt_to_player} damage")
                                else:
                                    print(f"You failed to flee and took {dmg_dealt_to_player} damage, killing you in the process")
                                    self.enemy.is_alive = False
                            action_completed = True
            
            else:
                dmg_dealt_to_player = self.enemy.attack(target=self.player)
                print(f"The {self.enemy.name} attacked you for {dmg_dealt_to_player} damage")

                if uniform(0, 1) < self.enemy.special_chance:
                    print(self.enemy.special_info)
                    self.enemy.use_special(self.enemy.special)
                
                if not self.player.is_alive:
                    print("You died")
                    break
            
            sleep(0.5)
            enemyturn = not enemyturn
        
        # if the combat ended and the enemy died: mark the room as cleared
        if not self.enemy.is_alive:
            self.map.get_room(self.player.position).is_cleared = True

        self.player.current_combat = None
        music.play("ambience")

def prompt_dice_roll():
    """Waits for the user to press enter"""
    input("[Press ENTER to roll dice]\n")

def get_player_action_options(player : Player, map : Map) -> list[str]:
    """Returns a list of strings containing the different actions the player can currently take"""

    current_room : Map.Room = map.get_room(player.position)
    door_options = [f"Open door facing {door_direction}" for door_direction in current_room.doors]

    default_action_options = [*door_options, "Open Inventory"]


    match current_room.type:
        case "empty":
            x, y = player.position
            if x == int(map.size/2) and y == int(map.size/2):
                print(choice(INTERACTION_DATA["start"]) + "\n")
            else:
                print(choice(INTERACTION_DATA["empty"]) + "\n")
            player_action_options = default_action_options

        case "enemy":
            # when the player moves, if the new room contains an enemy, a combat interaction is started right away, blocking main until finished
            # if we are here the enemy has already been slain
            player_action_options = default_action_options
        
        case "chest":
            # when the player moves, if the new room contains a chest, the room.chest_item property gets set right away
            # if is_cleared is True then the chest has already been looted
            if not current_room.is_cleared:
                player_action_options = [
                    "Open chest",
                    *door_options,
                    "Open Inventory"
                ]
            else:
                player_action_options = default_action_options

        case "trap":
            # when the player moves, if the new room contains a trap, the damage dialog is prompted right away
            # at this point the trap has been dealt with
            player_action_options = default_action_options

        case "mimic_trap":
            # if the mimic hasn't been triggered yet the room should look like a chest room
            if not current_room.is_cleared:
                player_action_options = [
                    "Open chest",
                    *door_options,
                    "Open Inventory"
                ]
            # if the mimic has been defeated
            else:
                player_action_options = default_action_options
        
        case "shop":
            player_action_options = [
                "Buy from shop",
                "Open Inventory",
                *door_options
            ]

    return player_action_options




def run_game():
    map = Map()
    player = Player(map)
    music = Music()
    music.play(type="ambience")

    map.open_UI_window(player_pos = player.position)

    while player.is_alive:
        print(f"{'='*15} New Round {'='*15}")

        # Get a list of the players currently available options and ask user to choose
        # Retry until a valid answer has been given
        action_options : list[str] = get_player_action_options(player, map)
        action_idx = get_user_action_choice("Choose action: ", action_options)

        # Decide what to do based on the player's choice
        match action_options[action_idx]:
            case "Open chest" | "Buy from shop":
                # interact with the current room
                map.get_room(player.position).interact(player, map, music)

            case "Open Inventory":
                player.open_inventory()

            case _other: # all other cases, aka Open door ...
                assert _other.startswith("Open door facing")
                door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing north" -> door_to_open = "north"
                map.move_player(direction=door_to_open, player=player, music=music)

        print()

    print("Game over")
    map.close_UI_window()



if __name__ == "__main__":
    run_game()


"""
init karta och UI karta
Titel



while True:
    input = Vad vill du göra
    if movement:
        Byt rum och starta vad som händer i rum
        if rum = monster:
            starta fight
        if rum = kista:
            ge item
        if rum = ...
    if inventory:
        visa inventory
        input = byt / släng saker

"""
