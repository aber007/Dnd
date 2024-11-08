import json
from random import choices
from UI_map_creation import create_UI_Map, update


CONSTANTS = {
    "map_base_size": 9,
    "player_base_inventory_size": 3,
    "player_base_hp": 6,
    "enemy_base_hp": 4,
    "enemy_base_dmg": 2,
    "items_config_file": "items.json"
}


class Entity:
    def take_damage(self, dmg : int):
        self.hp = max(0, self.hp - dmg)

class Player(Entity):
    def __init__(self, position : list[int,int]) -> None:
        self.position = position
        self.hp = CONSTANTS["player_base_hp"]
        self.active_dice_effects : list[int] = []
        
        self.inventory = Inventory(CONSTANTS["player_base_inventory_size"])

        self.current_enemy : Enemy | None = None
    
    def get_dice_modifier(self) -> int:
        return sum(self.active_dice_effects)
    
    def attack(self):
        self.inventory.equipped_weapon.use()

class Enemy(Entity):
    def __init__(self, player : Player) -> None:
        self.hp = CONSTANTS["enemy_base_hp"]
        self.dmg = CONSTANTS["enemy_base_dmg"]
        self.target = player
    
    def attack(self):
        self.player.take_damage(self.dmg)


class Map:
    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

    def __init__(self, size : int) -> None:
        """Generates the playable map"""
        
        if size % 2 == 0:
            size += 1
        self.starting_position = [int(size/2), int(size/2)]
        room_types = ["empty","enemy","chest","trap","shop"]
        probabilities = [0.25,0.5,0.2,0.1,0.05]
        "Initialize 2D array"
        rooms = [[0 for x in range(size)] for y in range(size)]
        

        "Assign random values to each location with set probabilites"
        for x in range(size):
            for y in range(size):
                if x == int(size/2) and y == int(size/2):
                    rooms[x][y] = Map.Room(type="empty", discovered=True, doors=["N", "S", "E", "W"])
                else:
                    roomtype = str(choices(room_types, probabilities)).removeprefix("['").removesuffix("']")
                    rooms[x][y] = Map.Room(type=roomtype, discovered=False, doors=["N", "S", "E", "W"])
        self.rooms = rooms
    
    def open_window(self) -> None:
        """Opens the playable map in a separate window"""

        "Press the map and then escape to close the window"
        create_UI_Map(CONSTANTS["map_base_size"], self.rooms)

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
        self.rooms[x][y].discovered = True
        update(self.rooms)
        






def get_player_action_options(player : Player, map : Map) -> list[str]:
    
    """Returns a list of strings containing the different actions the player can currently take"""    

    current_room : Map.Room = map.get_room(player.position)
    get_door_options_func = lambda current_room: [f"Open door facing {door_direction}" for door_direction in current_room.doors]


    match current_room.type:
        case "empty":
            player_action_options = [
                *get_door_options_func(current_room),
                "Open inventory"
            ]

        case "enemy":
            player_action_options = [
                "Attack",
                "Open inventory",
                "Attempt to flee"
            ]
        
        case "chest":
            player_action_options = [
                "Open chest",
                *get_door_options_func(current_room),
                "Open inventory"
            ]

        case "trap":
            player_action_options = [
                *get_door_options_func(current_room),
                "Open inventory"
            ]
        
        case "shop":
            player_action_options = [
                "Buy from shop",
                "Open inventory",
                *get_door_options_func(current_room)
            ]

    
    return player_action_options
    


def load_item_data_from_file() -> dict:
    with open(CONSTANTS["items_config_file"], "r") as f:
        file_contents = f.read()
    
    global items_data_dict
    items_data_dict = json.loads(file_contents)


def check_user_input_error(action_idx : str, action_options : list[str]) -> tuple[bool, str]:

    """Checks if the user's input is valid. If not: return (True, "error message"), otherwise: return (False, "")"""

    if not action_idx.isdigit():
        return (True, f"'{action_idx}' isn't a valid option")
    
    if not int(action_idx) < len(action_options):
        return (True, f"'{action_idx}' is out of range")
    
    return (False, "")

def run_game():
    map : Map = Map(CONSTANTS["map_base_size"])
    player = Player(map.starting_position)
    load_item_data_from_file()

    Map.open_window(map)


    while True:
        # Get a list of the players currently available options and print them to console
        action_options : list[str] = get_player_action_options(player, map)
        print("\n".join(f"{idx}) {action}" for idx,action in enumerate(action_options)))

        # Ask the player to choose an action and handle possible errors
        action_idx : str[int] = input("Choose action: ")
        err, err_message = check_user_input_error(action_idx, action_options)
        if err:
            print(err_message)
            continue

        # Decide what to do based on the players choice
        match action_options[int(action_idx)]:
            case "Attack":
                pass

            case "Open inventory":
                pass
            
            case "Attempt to flee":
                pass
            
            case "Open chest":
                pass # print to console f"You found {item.display_name}\n{item.description}"
            
            case "Buy from shop":
                pass

            case _other: # all other cases, aka Open door ...
                assert _other.startswith("Open door facing")
                door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing north" -> door_to_open = "north"
                Map.move_player(self=map, direction=door_to_open, player=player)
            



if __name__ == "__main__":
    from items import Item, Inventory
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