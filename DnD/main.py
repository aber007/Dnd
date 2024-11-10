from random import randint, choices, choice
from time import sleep
from .UI_map_creation import create_UI_Map, update
from . import (
    CONSTANTS,
    ENEMY_DATA,
    Item,
    Inventory,
    Vector2
    )



class Entity:
    def take_damage(self, dmg : int, return_text : bool = False) -> None:
        self.hp = max(0, self.hp - dmg)
        if return_text:
            if 0 < self.hp:
                self.on_damage_taken(dmg, self.hp)
            else:
                self.on_death(dmg)

class Player(Entity):
    def __init__(self, position : Vector2) -> None:
        self.position = position
        self.hp = CONSTANTS["player_base_hp"]
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
        Otherwise, returns only dice_result.
        """

        # get a random number between 0 and dice_base_sides then add the dice modifier
        # max() ensures the roll has a min value of 1
        dice_result = max(1, randint(1, CONSTANTS["dice_base_sides"]) + self.get_dice_modifier())
        self.active_dice_effects.clear()
        
        if success:
            return (success(dice_result), dice_result)
        else:
            return dice_result

    def attack(self) -> None:
        self.current_enemy.take_damage(self.inventory.equipped_weapon.dmg)

    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The player was hit for {dmg} damage\nPlayer hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The player was hit for {dmg} dmg and died")
        quit() # make proper "Game Over" thingy

class Enemy(Entity):
    def __init__(self, enemy_type : str, target : Player) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value wont be useful its not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.target = target
    
    def attack(self) -> None:
        self.target.take_damage(self.dmg)
    
    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The enemy was hit for {dmg} damage\nEnemy hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The enemy was hit for {dmg} damage and died")
        self.target.current_enemy = None
    def use_special(self, special : str) -> None:
        """Runs the code for special abilites which can be used during combat"""
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
            """Called right when the player enters the room. Eg. starts the trap interaction or decides a chest's item etc"""

            # the enemy spawn, chest_item decision and shop decisions should only happen once
            # the non-mimic trap should always trigger its dialog
            match (self.type, first_time_entering_room):
                case ("enemy", True):
                    Combat(player, map).start()

                case ("chest", True):
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
                        player.take_damage(CONSTANTS["normal_trap_base_dmg"])
        
        def interact(self, player : Player, map) -> None:
            """Called when the player chooses to interact with a room. Eg. opening a chest or opening a shop etc\n
            This is especially useful when dealing with the mimic trap as appears to be a chest room, thus tricking the player into interacting"""

            match self.type:
                case "chest":
                    pass # give player the chest_item, print to console f"You found {item.name_in_sentence}\n{item.description}"

                case "mimic_trap":
                    print("\nOh no! As you opened the chest you got ambushed by a Mimic!")
                    player.take_damage(CONSTANTS["mimic_trap_base_ambush_dmg"])
                    print()
                    Combat(player, map, force_enemy_type = "Mimic").start()
                
                case "shop":
                    pass # shop dialog


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
        

        # Assign random values to each location with set probabilites
        for x in range(self.size):
            for y in range(self.size):
                if x == int(self.size/2) and y == int(self.size/2):
                    rooms[x][y] = Map.Room(type="empty", discovered=True, doors=["N", "E", "S", "W"])
                else:
                    roomtype = str(choices(room_types, probabilities)).removeprefix("['").removesuffix("']")
                    rooms[x][y] = Map.Room(type=roomtype, discovered=False, doors=["N", "E", "S", "W"])
        self.rooms = rooms
    
    def open_window(self) -> None:
        """Opens the playable map in a separate window"""

        # Press the map and then escape to close the window
        create_UI_Map(self.size, self.rooms)
    
    def close_window(self):
        create_UI_Map(self.size, self.rooms, close=True)
        pass

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
        update(self.rooms)

        self.rooms[x][y].on_enter(player = player, map = self, first_time_entering_room = first_time_entering_room)


class Combat:
    def __init__(self, player : Player, map : Map, force_enemy_type : str | None = None) -> None:
        self.player = player
        self.map = map
        self.enemy = self.create_enemy(force_enemy_type)
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
        print(f"{'='*15} Combat {'='*15}")
        print(f"\nAn enemy appeared! It's {self.enemy.name_in_sentence}!")
        enemyturn = choice([True, False])
        
        while self.player.hp > 0 or self.enemy.hp > 0:
            self.turn += 1
            
            print(f"\n) Turn {self.turn} (")
            print(f"Player hp: {self.player.hp}")
            print(f"{self.enemy.name} hp: {self.enemy.hp} \n")

            if enemyturn == False:
                
                print("Choose action") #Actions will always be same, No need to be dynamic
                print("1) Attack")
                print("2) Open Inventory")
                print("3) Flee")
                actions = ["Attack", "Open Inventory", "Flee"]
                combat_action : str[int] = input("Choose action: ")
                err, err_message = check_user_input_error(combat_action, actions)
                if err:
                    print(err_message, end="\n\n")
                    continue
                match combat_action:
                    case "1":
                        enemyturn = True
                        pass
                    case "2":
                        print(self.player.inventory)
                        pass
                    case "3":
                        print("Attempting to flee, Roll 12 or higher to succeed")
                        prompt_dice_roll()
                        roll = self.player.roll_dice()
                        print(f"You rolled a {roll}")
                        if roll >= 12:
                            if roll < 15:      
                                self.player.take_damage(self.enemy.dmg)
                                if self.player.hp > 0:
                                    print(f"The {self.enemy.name} managed to hit you for {self.enemy.dmg} while fleeing\nPlayer hp remaining: {self.player.hp}")
                                else:
                                    print(f"The {self.enemy.name} managed to hit you for {self.enemy.dmg} while fleeing and you died")
                                    break
                            elif roll == 20:
                                print(f"You managed to scoop up a few coins while running out")
                                self.player.gold += self.enemy.gold // 2
                            print(f"You sucessfully fled the {self.enemy.name}")
                            break
                        else:
                            self.player.take_damage(self.enemy.dmg * 2)
                            if self.player.hp > 0:
                                print(f"You failed to flee and took {self.enemy.dmg * 2} damage")
                            else:
                                print(f"You failed to flee and took {self.enemy.dmg * 2} damage and you died")
                                break
                            enemyturn = True
            else:             
                enemyturn = False
                print(f"The {self.enemy.name} attacked you for {self.enemy.dmg} damage")
                self.enemy.attack()
                if randint(1,100) < self.enemy.special_chance*100:
                    print(self.enemy.special_info)
                    self.enemy.use_special(self.enemy.special)
                if self.player.hp <= 0:
                    print("You died")
                    break
            sleep(1)
        self.map.get_room(self.player.position).is_enemy_defeated = True

def prompt_dice_roll():
    """Waits for the user to press enter"""
    input("[Press ENTER to roll dice]\n")

def get_player_action_options(player : Player, map : Map) -> list[str]:
    """Returns a list of strings containing the different actions the player can currently take"""

    current_room : Map.Room = map.get_room(player.position)
    door_options = [f"Open door facing {door_direction}" for door_direction in current_room.doors]

    default_action_options = [*door_options, "Open inventory"]


    match current_room.type:
        case "empty":
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
                    "Open inventory"
                ]
            else:
                player_action_options = default_action_options

        case "trap":
            # when the player moves, if the new room contains a trap, the damage dialog is prompted right away
            # at this point the trap has been dealt with
            player_action_options = default_action_options
        
        case "mimic_trap":
            # if the mimic hasnt been triggered yet the room should look like a chest room
            if not current_room.is_enemy_defeated:
                player_action_options = [
                    "Open chest",
                    *door_options,
                    "Open inventory"
                ]
            # if the mimic has been defeated
            else:
                player_action_options = default_action_options
        
        case "shop":
            player_action_options = [
                "Buy from shop",
                "Open inventory",
                *door_options
            ]

    
    return player_action_options

def check_user_input_error(action_nr : str, action_options : list[str]) -> tuple[bool, str]:

    """Checks if the user's input is valid. If not: return (True, "error message"), otherwise: return (False, "")"""

    if not action_nr.isdigit():
        return (True, f"'{action_nr}' isn't a valid option")
    
    if not (0 < int(action_nr) <= len(action_options)):
        return (True, f"'{action_nr}' is out of range")
    
    return (False, "")




def run_game():
    map = Map()
    player = Player(map.starting_position)

    map.open_window()


    while True:
        if player.hp <= 0:
            print("Game over")           
            sleep(0.5)
            map.close_window()
            break

        print(f"{'='*15} New Round {'='*15}")

        # Get a list of the players currently available options and print them to console
        action_options : list[str] = get_player_action_options(player, map)
        print("\n".join(f"{idx+1}) {action}" for idx,action in enumerate(action_options)))

        # Ask the player to choose an action and handle possible errors
        # action_nr starts at 1
        action_nr : str[int] = input("Choose action: ")
        err, err_message = check_user_input_error(action_nr, action_options)
        if err:
            print(err_message, end="\n\n")
            continue

        # Decide what to do based on the player's choice
        match action_options[int(action_nr)-1]:
            case "Open chest" | "Buy from shop":
                # interact with the current room
                map.get_room(player.position).interact(player, map)

            case "Open inventory":
                pass
            
            case "Attempt to flee":
                pass

            case _other: # all other cases, aka Open door ...
                assert _other.startswith("Open door facing")
                door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing north" -> door_to_open = "north"
                map.move_player(direction=door_to_open, player=player)
        
        print()

           



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
