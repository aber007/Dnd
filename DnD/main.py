from random import randint, choices
from time import sleep
from . import CONSTANTS, Item, Inventory
from .UI_map_creation import create_UI_Map, update



class Entity:
    def take_damage(self, dmg : int) -> None:
        self.hp = max(0, self.hp - dmg)

        if 0 < self.hp:
            self.on_damage_taken(dmg, self.hp)
        else:
            self.on_death(dmg)

class Player(Entity):
    def __init__(self, position : list[int,int]) -> None:
        self.position = position
        self.hp = CONSTANTS["player_base_hp"]
        self.active_dice_effects : list[int] = []
        
        self.inventory = Inventory(CONSTANTS["player_base_inventory_size"])

        self.current_enemy : Enemy | None = None
    
    def get_dice_modifier(self) -> int:
        return sum(self.active_dice_effects)
    
    def roll_dice(self, success : callable) -> tuple[bool,int]:
        """Roll the dice and include any dice modifiers.
        success is a function that, given dice_result, returns a bool.
        return (success function result, dice result)"""

        # get a random number between 0 and dice_base_sides then add the dice modifier
        # max() ensures the roll has a min value of 1
        dice_result = max(1, randint(1, CONSTANTS["dice_base_sides"]) + self.get_dice_modifier())
        self.active_dice_effects.clear()
        
        return (success(dice_result), dice_result)

    def attack(self) -> None:
        self.current_enemy.take_damage(self.inventory.equipped_weapon.dmg)

    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The player was hit for {dmg} damage\nPlayer hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The player was hit for {dmg} dmg and died")
        quit() # make proper "Game Over" thingy

class Enemy(Entity):
    def __init__(self, target : Player) -> None:
        self.hp = CONSTANTS["enemy_base_hp"]
        self.dmg = CONSTANTS["enemy_base_dmg"]
        self.target = target
    
    def attack(self) -> None:
        self.target.take_damage(self.dmg)
    
    def on_damage_taken(self, dmg : int, remaining_hp : int) -> None:
        print(f"The enemy was hit for {dmg} damage\nEnemy hp remaining: {remaining_hp}")

    def on_death(self, dmg : int) -> None:
        print(f"The enemy was hit for {dmg} damage and died")
        self.target.current_enemy = None



class Map:
    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.chest_item : Item | None = None
            self.is_mimic : bool | None = None
        
        def on_enter(self, player : Player, first_time_entering_room : bool) -> None:
            """Called right when the player enters the room. Eg. starts the non-mimic trap interaction or decides a chest's item etc"""

            # the enemy spawn, chest_item decision and shop decisions should only happen once
            # the non-mimic trap should always trigger its dialog
            match (self.type, first_time_entering_room):
                case ("enemy", True):
                    player.current_enemy = Enemy(target=player)
                    print("An enemy appeared")

                case ("chest", True):
                    pass # decide chest item

                case ("shop", True):
                    pass # decide shop's wares/prices?

                case ("trap", _):
                    if not self.is_mimic:
                        print(f"You stepped in a trap! Roll at least {CONSTANTS["normal_trap_base_min_roll_to_escape"]} to save yourself")
                        prompt_dice_roll()
                        success, dice_result = player.roll_dice(success=lambda dice_result : CONSTANTS["normal_trap_base_min_roll_to_escape"] <= dice_result)

                        if success:
                            print(f"You rolled {dice_result} and managed to escape unharmed")
                        else:
                            print(f"You rolled {dice_result} and was harmed by the trap while trying to escape")
                            player.take_damage(CONSTANTS["trap_base_dmg"])
        
        def interact(self, player : Player) -> None:
            """Called when the player chooses to interact with a room. Eg. opening a chest or attacking an enemy etc\n
            This is especially useful when dealing with the mimic trap as appears to be a chest room, thus tricking the player into interacting"""

            match self.type:
                case "enemy":
                    player.attack()

                case "chest":
                    pass # give player the chest_item, print to console f"You found {item.display_name}\n{item.description}"

                case "trap":
                    assert self.is_mimic # if not mimic we shouldnt be here

                    # if player.current_enemy is None then the mimic-trap hasn't triggered yet
                    if player.current_enemy == None:
                        print("Oh no! As you opened the chest you got ambushed by a mimic!")
                        player.take_damage(CONSTANTS["mimic_trap_base_ambush_dmg"])
                        player.current_enemy = Enemy(target=player)
                    else:
                        player.attack()

                case "shop":
                    pass # shop dialog


    def __init__(self, size : int = CONSTANTS["map_base_size"]) -> None:
        """Generates the playable map"""
        self.size = size
        
        if self.size % 2 == 0:
            self.size += 1
        self.starting_position = [int(self.size/2), int(self.size/2)]
        room_types = ["empty","enemy","chest","trap","shop"]
        probabilities = [0.25,0.5,0.2,0.1,0.05]
        "Initialize 2D array"
        rooms = [[0 for x in range(self.size)] for y in range(self.size)]
        

        "Assign random values to each location with set probabilites"
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

        "Press the map and then escape to close the window"
        create_UI_Map(self.size, self.rooms)

    def get_room(self, position : list[int,int]) -> Room:
        """Using an x and a y value, return a room at that position"""
        return self.rooms[position[0]][position[1]]
    
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

        player.position = [x, y]

        first_time_entering_room = not self.rooms[x][y].discovered
        self.rooms[x][y].discovered = True
        update(self.rooms)

        self.rooms[x][y].on_enter(player = player, first_time_entering_room = first_time_entering_room)



def prompt_dice_roll():
    """Waits for the user to press enter"""
    input("[Press ENTER to roll dice}")


def get_player_action_options(player : Player, map : Map) -> list[str]:
    
    """Returns a list of strings containing the different actions the player can currently take"""    

    current_room : Map.Room = map.get_room(player.position)
    door_options = [f"Open door facing {door_direction}" for door_direction in current_room.doors]

    default_action_options = [*door_options, "Open inventory"]


    match current_room.type:
        case "empty":
            player_action_options = default_action_options

        case "enemy":
            # when the player moves, if the new room contains an enemy, the player.current_enemy property gets set right away
            # if player.current_enemy is None then the enemy has already been slain
            if player.current_enemy != None:
                player_action_options = [
                    "Attack",
                    "Open inventory",
                    "Attempt to flee"
                ]
            
            else:
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
            # when the player moves, if the new room contains a non-mimic trap, the damage dialog is ran right away
            # at this point the non-mimic trap has been dealt with
            # if the new room contains a mimic trap, give the player the same options as if the room contained a chest
            if not current_room.is_mimic:
                player_action_options = [
                    *door_options,
                    "Open inventory"
                ]
            else:
                player_action_options = [
                    "Open chest TEMP mimic",
                    *door_options,
                    "Open inventory"
                ]
        
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

        # Decide what to do based on the players choice
        current_room = map.get_room(player.position)
        match action_options[int(action_nr)-1]:
            case "Attack" | "Open chest" | "Buy from shop":
                current_room.interact(player)

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