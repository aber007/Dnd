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
    Array2D,
    get_user_action_choice,
    ensure_terminal_width,
    wait_for_key
    )

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager



class Entity:
    def take_damage(self, dmg : int) -> int:
        if isinstance(self, Enemy):    dmg -= max(0, self.defence_melee)
        elif isinstance(self, Player): dmg -= max(0, self.defence)
        
        self.hp = max(0, self.hp - dmg)
        self.is_alive = 0 < self.hp
        
        return dmg

class Player(Entity):
    def __init__(self, parent_map) -> None:
        self.parent_map : Map = parent_map
        self.position : Vector2 = self.parent_map.starting_position

        # combat related attributes
        self.is_alive = True
        self.hp = CONSTANTS["player_hp"]
        self.defence = CONSTANTS["player_base_defence"]
        self.current_combat : Combat | None = None

        # progression related attributes
        self.inventory = Inventory()

        self.active_dice_effects : list[int] = []
    
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

    class ReachableRoom:
        """A simple version of Map.Room that's used when generating room doors"""

        def __init__(self) -> None:
            self.doors : list[str] = []
            self.reachable : bool = False

    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.chest_item : Item | None = None
            self.is_cleared : bool = False
            self.shop_items : list[Item] = []

        def on_enter(self, player : Player, map, first_time_entering_room : bool, music : Music) -> None:
            """Called right when the player enters the room. E.g. starts the trap interaction or decides a chest's item etc"""

            match self.type:
                case "shop":  music.play("shop")
                case "enemy": music.play("fight")
                case _:       music.play("ambience")

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
                    print("\n" + choice(INTERACTION_DATA["chest"]))

                case ("shop", True):
                    print("\n" + choice(INTERACTION_DATA["shop"]))

                    possible_items = list(ITEM_DATA.keys())
                    item_probabilites = [ITEM_DATA[item_id]["probability"] for item_id in possible_items]

                    shop_item_ids = choices(possible_items, item_probabilites, k=CONSTANTS["shop_item_count"])
                    for item_id in shop_item_ids:
                        item = Item(item_id)
                        item.current_price = item.base_price + randint(item.base_price // -CONSTANTS["shop_item_price_range_divider"], item.base_price // CONSTANTS["shop_item_price_range_divider"])
                        self.shop_items.append(item)

                case ("trap", _):
                    print(f"\nYou stepped in a trap! Roll at least {CONSTANTS['normal_trap_min_roll_to_escape']} to save yourself")
                    wait_for_key("[Press ENTER to roll dice]\n", "enter")
                    roll = player.roll_dice()

                    if CONSTANTS["normal_trap_min_roll_to_escape"] <= roll:
                        print(f"You rolled {roll} and managed to escape unharmed")
                    else:
                        print(f"You rolled {roll} and was harmed by the trap while escaping")
                        dmg_taken = player.take_damage(CONSTANTS["normal_trap_dmg"])
                        print(f"The player took {dmg_taken} damage. {player.hp} HP remaining")
            
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
                    # stay in the shop menu until the player explicitly chooses to Leave
                    while True:
                        print(f"\n{'='*15} SHOP {'='*15}")
                        print(f"\nCurrent gold: {player.inventory.gold}")
                        print("\nAvalible items:")
                        shop_options = [f"{item.name}: {item.current_price} gold" for idx,item in enumerate(self.shop_items)]
                        shop_options += ["Open Inventory", "Leave"]
                        
                        shop_option_idx = get_user_action_choice("Choose item to buy: ", shop_options)
                        match shop_options[shop_option_idx]:
                            case "Open Inventory":
                                player.open_inventory()

                            case "Leave":
                                break

                            case _other:
                                # the player chose an item to buy
                                selected_item = self.shop_items[shop_option_idx]

                                # if the player can afford the item
                                if selected_item.current_price < player.inventory.gold:
                                    player.inventory.gold -= selected_item.current_price
                                    player.inventory.receive_item(selected_item)
                                    self.shop_items.remove(selected_item)

                                else:
                                    print("\nYou do not have enough gold to buy this item")
                        
                        if len(self.shop_items) == 0:
                            print("This shop is out of items")
                            self.is_cleared = True
                            break
            
            # update the tile the player just interacted with
            player.parent_map.UI_instance.send_command("tile", player.position, player.parent_map.decide_room_color(player.position))

    class UI:
        def __init__(self, size, rooms) -> None:
            # to be set by the parent Map object
            self.size : int = size
            self.rooms : Array2D[Map.Room] = rooms

            self.manager = Manager()
            self.command_queue = self.manager.Queue(maxsize=100)
            self.UI_thread : Process | None = None
        
        def open(self, player_pos : Vector2):
            self.UI_thread = Process(target=openUIMap, args=(self.size, self.rooms, player_pos, self.command_queue))
            self.UI_thread.start()
        
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
        self.starting_position = Vector2(double=self.size//2)
        room_types = list(CONSTANTS["room_probabilities"].keys())
        probabilities = list(CONSTANTS["room_probabilities"].values())

        
        def get_doors_for_room(x,y):
            """Get the doors for room depending on coords. Doors facing non-existant rooms outside the map are removed"""

            doors = ["N", "E", "S", "W"]
            xy_max = self.size-1

            if x == 0: doors.remove("W")
            elif x == xy_max: doors.remove("E")

            if y == 0: doors.remove("N")
            elif y == xy_max: doors.remove("S")

            return doors
        
        def recursive_check_room_reachable(rooms : Array2D[Map.ReachableRoom], current_position: Vector2):
            current_room : Map.ReachableRoom = rooms[current_position]

            # if the recursive check has already been here then all rooms are already queued to be searched
            if current_room.reachable:
                return
            
            current_room.reachable = True

            for door in current_room.doors:
                next_position = current_position + CONSTANTS["directional_coord_offsets"][door]
                recursive_check_room_reachable(rooms, next_position)

        # Initialize 2D array
        self.rooms : Array2D = Array2D.create_frame_by_size(
            width = self.size,
            height = self.size,
            val_callable = lambda : Map.ReachableRoom())

        # generate new door configurations until every single room is reachable
        # usually takes an avrg of 2 tries to find a successful configuration
        #     during testing the mean time for 10000 successful map generations was 1.5 ms with remove_door_percent = 0.3 (time isnt an issue)
        while True:
            # set the doors for each room. take into account wether the room is on the edge of the map or not
            for x, y, _ in self.rooms:
                self.rooms[x,y].doors = get_doors_for_room(x, y)
            
            # if debug is enabled dont remove any doors
            if not CONSTANTS["debug"]["remove_room_doors"]:
                break

            # removes 1 door from remove_door_percent% of all rooms
            # also removes the corresponding door in the room behind the door which was deleted
            remove_door_count = int(self.size**2 * CONSTANTS["remove_door_percent"])
            for _ in range(remove_door_count):
                x = randint(0, self.rooms.size.x-1)
                y = randint(0, self.rooms.size.y-1)

                selected_room = self.rooms[x,y]

                # if a room has 0 doors, which can happen if many doors are removed from
                # the same area, redo the map gen
                if len(selected_room.doors) == 0:
                    break

                door_to_remove = choice(selected_room.doors)
                
                # removing the opposite facing door in the room behind door_to_remove. this ensures all doors are bi-directional
                room_behind_door_to_remove = self.rooms[Vector2(x,y) + CONSTANTS["directional_coord_offsets"][door_to_remove]]
                opposite_door_to_remove = {"N": "S", "E": "W", "S": "N", "W": "E"}[door_to_remove]

                selected_room.doors.remove(door_to_remove)
                room_behind_door_to_remove.doors.remove(opposite_door_to_remove)
            
            # go through each room and set .reachable = True if its reachable
            recursive_check_room_reachable(self.rooms, self.starting_position)

            # if all rooms are reachable, break the loop
            if all([val.reachable for _, _, val in self.rooms]):
                break

        # turn the Map.ReachableRoom objects into Map.Room object, inheriting the generated doors
        for x, y, reachable_room in self.rooms:
            if (x, y) == self.starting_position:
                self.rooms[x,y] = Map.Room(type="empty", discovered=True, doors=reachable_room.doors)
            else:
                roomtype = choices(room_types, probabilities)[0]
                self.rooms[x,y] = Map.Room(type=roomtype, discovered=False, doors=reachable_room.doors)
        
        if CONSTANTS["debug"]["print_map"]:
            last_y = 0
            for x, y, room in self.rooms:
                if y != last_y: print() ; last_y = y
                print(f" [{x},{y},{room.type},{''.join(room.doors)}] ".ljust(22, " "), end="")
            print("\n")

        self.UI_instance = Map.UI(self.size, self.rooms)

    
    def open_UI_window(self, player_pos : Vector2) -> None:
        """Opens the playable map in a separate window"""

        # Press the map and then escape to close the window
        self.UI_instance.open(player_pos)
    
    def close_UI_window(self) -> None:
        self.UI_instance.close()

    def get_room(self, position : Vector2) -> Room:
        """Using an x and a y value, return a room at that position"""
        return self.rooms[position]
    
    def decide_room_color(self, room_position : Vector2) -> str:
        room : Map.Room = self.get_room(room_position)
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
                return colors["discovered"] if room.is_cleared else colors["shop"]



    def move_player(self, direction : str, player : Player, music : Music) -> None:
        """Move the player in the given direction"""

        player.position += CONSTANTS["directional_coord_offsets"][direction]
        new_current_room = self.get_room(player.position)

        first_time_entering_room = not new_current_room.discovered
        new_current_room.discovered = True
        
        self.UI_instance.send_command("tile", player.position, self.decide_room_color(player.position))
        self.UI_instance.send_command("pp", player.position)

        new_current_room.on_enter(player = player, map = self, first_time_entering_room = first_time_entering_room, music=music)


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

    def start(self, music : Music) -> None:
        self.player.current_combat = self

        print(f"\n{'='*15} COMBAT {'='*15}")
        
        story_text_enemy = str(choice(INTERACTION_DATA["enemy"]))
        if "enemy" in story_text_enemy:
            print(story_text_enemy.replace("enemy", self.enemy.name_in_sentence))
        else:
            print(story_text_enemy)
            print(f"\nAn enemy appeared! It's {self.enemy.name_in_sentence}!")
        
        enemyturn = choice([True, False])

        
        fled = False
        while self.player.is_alive and self.enemy.is_alive and not fled:
            self.turn += 1

            print(f"\n--------------) Turn {self.turn} (--------------")
            print(f"Player hp: {self.player.hp}")
            print(f"{self.enemy.name} hp: {self.enemy.hp}\n")

            if not enemyturn:
                fled = self.player_turn()
            else:
                self.enemy_turn()
            
            sleep(1)
            enemyturn = not enemyturn
        
        # if the combat ended and the enemy died: mark the room as cleared
        if not self.enemy.is_alive:
            story_text_enemy_defeated = str(choice(INTERACTION_DATA["enemy_defeated"]))
            print("\n" + story_text_enemy_defeated.replace("enemy", self.enemy.name))
            print(f"You picked up {self.enemy.gold} gold from the {self.enemy.name}")
            print(f"You earned {self.enemy.exp} EXP from this fight\n")

            self.map.get_room(self.player.position).is_cleared = True

            self.player.inventory.gold += self.enemy.gold
            self.player.inventory.exp += self.enemy.exp
            self.player.inventory.check_lvl()
            

        self.player.current_combat = None
        music.play("ambience")

    def player_turn(self) -> bool:
        """If the player attempted to flee: return the result, otherwise False"""

        fled = False
        action_completed = False  # Loop control variable to retry actions
        while not action_completed:
            action_options = ["Use item / Attack", "Attempt to Flee"]
            action_idx = get_user_action_choice("Choose action: ", action_options)

            match action_options[action_idx]:                   
                case "Use item / Attack":
                    action_completed = self.player_use_item_attack()

                case "Attempt to Flee":
                    fled = self.player_attempt_to_flee()
                    action_completed = True
        
        return fled

    def player_use_item_attack(self) -> bool:
        """Returns wether the player used an item or not, aka action_completed"""
        action_completed = False

        # item_return is either tuple[dmg done, item name_in_sentence] or None, depending on if any damage was done
        item_return = self.player.open_inventory()
        if item_return is not None:
            dmg, item_name_in_sentence = item_return
            dmg_dealt = self.enemy.take_damage(dmg)

            print(f"\nThe {self.enemy.name} was hurt by the player using {item_name_in_sentence}")
            print(f"\nYou attacked the {self.enemy.name} for {dmg_dealt} damage")

            action_completed = True
        
        return action_completed

    def player_attempt_to_flee(self) -> bool:
        """Returns wether the attempt to flee was successful"""
        fled = False

        print("Attempting to flee, Roll 12 or higher to succeed")

        wait_for_key("[Press ENTER to roll dice]", "enter")
        roll = self.player.roll_dice()
        
        print(f"\nYou rolled {roll}")

        # if you managed to escape
        if CONSTANTS["flee_min_roll_to_escape"] <= roll:
            # if the enemy hit you on your way out
            if roll < CONSTANTS["flee_min_roll_to_escape_unharmed"]:
                dmg_dealt_to_player = self.enemy.attack(target=self.player)
                
                if self.player.is_alive:
                    print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing\nPlayer hp remaining: {self.player.hp}")
                else:
                    print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing, killing you in the process")
            
            # if you escaped with coins
            elif CONSTANTS["flee_exact_roll_to_escape_coins"] <= roll:
                print(choice(INTERACTION_DATA["escape_20"]))
                self.player.inventory.gold += self.enemy.gold // CONSTANTS["flee_20_coins_to_receive_divider"]
            
            print(choice(INTERACTION_DATA["escape"]))
            fled = True

        # if you didnt escape
        else:
            dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=2)

            if self.player.is_alive:
                print(f"You failed to flee and took {dmg_dealt_to_player} damage\nPlayer hp remaining: {self.player.hp}")
            else:
                print(f"You failed to flee and took {dmg_dealt_to_player} damage, killing you in the process")
        
        return fled
    
    def enemy_turn(self):
        dmg_dealt_to_player = self.enemy.attack(target=self.player)

        if self.player.is_alive:
            print(f"The {self.enemy.name} attacked you for {dmg_dealt_to_player} damage\nPlayer hp remaining: {self.player.hp}")
        else:
            print(f"The {self.enemy.name} attacked you for {dmg_dealt_to_player} damage, killing you in the process")
            return
        
        if uniform(0, 1) < self.enemy.special_chance:
            print(self.enemy.special_info)
            self.enemy.use_special(self.enemy.special)

            # *player takes dmg from the special*



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
    ensure_terminal_width(CONSTANTS["min_desired_terminal_width"])

    map = Map()
    player = Player(map)
    music = Music()

    map.open_UI_window(player_pos = player.position)

    while player.is_alive and player.inventory.lvl < 10:
        if not CONSTANTS["debug"]["disable_console_clearing"]:
            # clears entire console and sets cursor pos top left
            print("\033[2J\033[H", end="")
        
        print(f"{'='*15} NEW ROUND {'='*15}", end="\n"*2)

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

        # print()
        # prompt_continue()
        wait_for_key("\n[Press ENTER to continue]\n", "enter")

    if not player.is_alive:
        print("\nGame over")
    
    else:
        print("\n" + "Congratulations! You escaped the castle or something.")

        #Add stats and print them here

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
