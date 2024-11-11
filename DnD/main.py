import os
from random import randint, choices, choice, uniform
from time import sleep
from .story import play, stop
from .UI_map_creation import openUIMap, Process, Manager
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


class Entity:
    def take_damage(self, dmg : int, log : bool = False) -> None:
        self.hp = max(0, self.hp - dmg)
        self.is_alive = 0 < self.hp
        if log:
            if 0 < self.hp:
                self.on_damage_taken(dmg, self.hp)
            else:
                self.on_death(dmg)
        
        return dmg

class Player(Entity):
    def __init__(self, position : Vector2) -> None:
        self.position = position
        self.hp = CONSTANTS["player_base_hp"]
        self.is_alive = True
        self.gold = CONSTANTS["player_starting_gold"]
        self.active_dice_effects : list[int] = []
        
        self.inventory = Inventory(CONSTANTS["player_base_inventory_size"])

        # self.current_enemy : Enemy | None = None
    
    def get_dice_modifier(self) -> int:
        return sum(self.active_dice_effects)
    
    def roll_dice(self, success : callable = None) -> tuple[bool,int] | int:
        """
        Roll the dice and include any dice modifiers.
        If success is provided, it should be a function that takes dice_result and returns a bool.
        If success is provided, returns (success function result, dice result).
        Otherwise, return only dice_result.
        """

        # get a random number between 0 and dice_base_sides then add the dice modifier
        # max() ensures the roll has a min value of 1
        dice_result = max(1, randint(1, CONSTANTS["dice_base_sides"]) + self.get_dice_modifier())
        self.active_dice_effects.clear()

        if success:
            return (success(dice_result), dice_result)
        else:
            return dice_result

    def attack(self, target, dmg_multiplier : int = 1) -> int:
        """Attack target your weapons damage  dmg_multiplier. The damage dealt is returned"""
        return target.take_damage(self.inventory.equipped_weapon.dmg * dmg_multiplier)

    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The player was hit for {dmg} damage\nPlayer hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The player was hit for {dmg} dmg and died")

class Enemy(Entity):
    def __init__(self, enemy_type : str, target : Player) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value won't be useful it's not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.is_alive = True
    
    def attack(self, target, dmg_multiplier : int = 1) -> int:
        """Attack target with base damage * dmg_multiplier. The damage dealt is returned"""
        return target.take_damage(self.dmg * dmg_multiplier)

    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The enemy was hit for {dmg} damage\nEnemy hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The enemy was hit for {dmg} damage and died")
    
    def use_special(self, special : str) -> None:
        """Runs the code for special abilities which can be used during combat"""
        pass


class Map:
    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.chest_item : Item | None = None
            self.is_enemy_defeated : bool | None = None



        def on_enter(self, player : Player, map, first_time_entering_room : bool) -> None:
            """Called right when the player enters the room. E.g. starts the trap interaction or decides a chest's item etc"""

            # the enemy spawn, chest_item decision and shop decisions should only happen once
            # the non-mimic trap should always trigger its dialog
            match (self.type, first_time_entering_room):
                case ("enemy", True):
                    Combat(player, map).start()

                case ("chest", True):
                    possible_items = list(ITEM_DATA.keys())
                    item_probabilites = []
                    for item in possible_items:
                        item_probabilites.append(ITEM_DATA[item]["probability"])
                    self.chest_item = str(choices(possible_items, item_probabilites)).removeprefix("['").removesuffix("']")
                    print(choice(INTERACTION_DATA["chest"])
)
                    pass # decide chest item

                case ("shop", True):
                    pass # decide shop's wares/prices?

                case ("trap", _):
                    print(f"\nYou stepped in a trap! Roll at least {CONSTANTS['normal_trap_base_min_roll_to_escape']} to save yourself")
                    prompt_dice_roll()
                    success, dice_result = player.roll_dice(success=lambda dice_result : CONSTANTS["normal_trap_base_min_roll_to_escape"] <= dice_result)

                    if success:
                        print(f"You rolled {dice_result} and managed to escape unharmed")
                    else:
                        print(f"You rolled {dice_result} and was harmed by the trap while escaping")
                        player.take_damage(CONSTANTS["normal_trap_base_dmg"], log=True)
        
        def interact(self, player : Player, map) -> None:
            """Called when the player chooses to interact with a room. E.g. opening a chest or opening a shop etc\n
            This is especially useful when dealing with the mimic trap as appears to be a chest room, thus tricking the player into interacting"""

            match self.type:
                case "chest":
                    print(f"You found {ITEM_DATA[self.chest_item]['name_in_sentence']}\n{ITEM_DATA[self.chest_item]['description']}")
                    player.inventory.receive_item(self.chest_item)
                    pass # give player the chest_item, print to console f"You found {item.name_in_sentence}\n{item.description}"

                case "mimic_trap":
                    print()
                    print(choice(INTERACTION_DATA["mimic"]))
                    player.take_damage(CONSTANTS["mimic_trap_base_ambush_dmg"], log=True)
                    print()
                    Combat(player, map, force_enemy_type = "Mimic").start()

                case "shop":
                    pass # shop dialog


    class UI:
        def __init__(self, size, rooms) -> None:
            # to be set by the parent Map object
            self.size : int = size
            self.rooms : list[list[Map.Room]] = rooms

            self.manager = Manager()
            self.command_queue = self.manager.Queue(100)
            self.UI_thread : Process | None = None
        
        def open(self):
            self.UI_thread = Process(target=openUIMap, args=(self.size, self.rooms, self.command_queue))
            self.UI_thread.start()
            sleep(0.5)
        
        def update(self, tile_position : Vector2, new_bg_color : str):
            self.command_queue.put_nowait(f"{tile_position.x},{tile_position.y} {new_bg_color}")
        
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
                    rooms[x][y] = Map.Room(type="empty", discovered=True, doors=["N", "E", "S", "W"])
                else:
                    roomtype = str(choices(room_types, probabilities)).removeprefix("['").removesuffix("']")
                    rooms[x][y] = Map.Room(type=roomtype, discovered=False, doors=["N", "E", "S", "W"])
        self.rooms = rooms

        self.UI_instance = Map.UI(self.size, self.rooms)
    
    def open_UI_window(self) -> None:
        """Opens the playable map in a separate window"""

        # Press the map and then escape to close the window
        self.UI_instance.open()
    
    def close_UI_window(self) -> None:
        self.UI_instance.close()

    def get_room(self, position : Vector2) -> Room:
        """Using an x and a y value, return a room at that position"""
        return self.rooms[position.x][position.y]
    
    def move_player(self, direction : str, player : Player) -> None:
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
        self.UI_instance.update(player.position, "gray")

        self.rooms[x][y].on_enter(player = player, map = self, first_time_entering_room = first_time_entering_room)


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
        """Adjust probabilites depending on distance away from spawn and difficulty of enemy"""
        for enemy_type in enemy_types:
            if ENEMY_DATA[enemy_type]["probability"] == 0:
                new_probability = distace_from_spawn * ((100-ENEMY_DATA[enemy_type]["exp"])/1000)
                spawn_probabilities[enemy_type] += new_probability

        enemy_type_to_spawn = str(choices(list(spawn_probabilities.keys()), list(spawn_probabilities.values()))).removeprefix("['").removesuffix("']")

        return Enemy(enemy_type = enemy_type_to_spawn, target = self.player)


    def start(self):
        # remember to deal with Enemy.on_damage_taken, Enemy.on_death, Player.on_damage_taken, Player.on_death
        stop()
        play("fight.mp3")
        print(f"{'='*15} Combat {'='*15}")
        story_text_enemy = str(choice(INTERACTION_DATA["enemy"]))
        if "enemy" in story_text_enemy:
            story_text_enemy.replace("enemy", self.enemy.name_in_sentence)
            print(story_text_enemy.replace("enemy", self.enemy.name_in_sentence))
        else:
            print(story_text_enemy)
            print(f"\nAn enemy appeared! It's {self.enemy.name_in_sentence}!")
        enemyturn = choice([True, False])

        while self.player.is_alive and self.enemy.is_alive:
            self.turn += 1

            print(f"\n) Turn {self.turn} (")
            print(f"Player hp: {self.player.hp}")
            print(f"{self.enemy.name} hp: {self.enemy.hp} \n")

            if not enemyturn:
                action_options = ["Attack", "Open Inventory", "Attempt to Flee"]
                action_nr = get_user_action_choice("Choose action: ", action_options)

                match action_options[int(action_nr)-1]:
                    case "Attack":
                        dmg_dealt = self.player.attack(target=self.enemy)
                        print(f"\nYou attacked the {self.enemy.name} for {dmg_dealt} damage")
                    
                    case "Open Inventory":
                        print(self.player.inventory)
                        # item_to_use = self.player.inventory.select_item()
                        # item_to_use.use()
                    
                    case "Attempt to Flee":
                        print("Attempting to flee, Roll 12 or higher to succeed")
                        prompt_dice_roll()
                        roll = self.player.roll_dice()
                        print(f"You rolled a {roll}")

                        # if you managed to escape
                        if 12 <= roll:
                            # if the enemy hit you on your way out
                            if roll < 15:
                                self.enemy.attack(target=self.player)
                                if self.player.is_alive:
                                    print(f"The {self.enemy.name} managed to hit you for {self.enemy.dmg} while fleeing\nPlayer hp remaining: {self.player.hp}")
                                else:
                                    print(f"The {self.enemy.name} managed to hit you for {self.enemy.dmg} while fleeing, killing you in the process")
                                    break
                            
                            # if you escaped with coins
                            elif roll == 20:
                                print(choice(INTERACTION_DATA["escape_20"]))
                                self.player.gold += self.enemy.gold // 2
                            print(choice(INTERACTION_DATA["escape"]))
                            break

                        # if you didnt escape
                        else:
                            self.enemy.attack(target=self.player, dmg_multiplier=2)
                            if self.player.is_alive:
                                print(f"You failed to flee and took {self.enemy.dmg * 2} damage")
                            else:
                                print(f"You failed to flee and took {self.enemy.dmg * 2} damage, killing you in the process")
                                break
            
            else:
                print(f"The {self.enemy.name} attacked you for {self.enemy.dmg} damage")
                self.enemy.attack(target=self.player)

                if uniform(0, 1) < self.enemy.special_chance:
                    print(self.enemy.special_info)
                    self.enemy.use_special(self.enemy.special)
                
                if not self.player.is_alive:
                    print("You died")
                    break
            
            sleep(1)
            enemyturn = not enemyturn
        
        self.map.get_room(self.player.position).is_enemy_defeated = True
        play("test.wav")

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
            # if room.chest_item is None then the chest has already been looted
            if current_room.chest_item != None:
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
            if not current_room.is_enemy_defeated:
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
    player = Player(map.starting_position)
    map.open_UI_window()
    play("test.wav")
    while player.hp > 0:
        
        print(f"{'='*15} New Round {'='*15}")

        # Get a list of the players currently available options and ask user to choose
        # Retry until a valid answer has been given
        action_options : list[str] = get_player_action_options(player, map)
        action_nr = get_user_action_choice("Choose action: ", action_options)

        # Decide what to do based on the player's choice
        match action_options[int(action_nr)-1]:
            case "Open chest" | "Buy from shop":
                # interact with the current room
                map.get_room(player.position).interact(player, map)

            case "Open Inventory":
                print(player.inventory)
                print("Choose item?")

            case _other: # all other cases, aka Open door ...
                assert _other.startswith("Open door facing")
                door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing north" -> door_to_open = "north"
                map.move_player(direction=door_to_open, player=player)

        print()

    print("Game over")
    map.open_UI_window()



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
