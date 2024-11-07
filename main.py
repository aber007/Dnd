

from random import choices
from UI_map_creation import create_UI_Map

CONSTANTS = {
    "map_base_size": 7,

    "player_inventory_size": 3,
    "player_base_hp": 5
}

class Item:
    pass

class Inventory:
    def __init__(self, size : int) -> None:
        self.size = size
        self.slots : dict[int, Item | None] = {slot_idx : None for slot_idx in range(size)}

class Player:
    def __init__(self, base_hp : int, position : tuple[int,int]) -> None:
        self.position = position

        self.base_hp = base_hp
        self.hp = base_hp
        
        self.inventory = Inventory(CONSTANTS["player_inventory_size"])


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
        self.starting_position = (int(size/2), int(size/2))
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

    def get_room(self, position : tuple) -> Room:
        """Using an x and a y value, return a room at that position or None"""
        return self.rooms[position[0]][position[1]]





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
                "Open inventory",
                *get_door_options_func(current_room)
            ]
        case "shop":
            player_action_options = [
                "Open inventory",
                "Buy from shop",
                *get_door_options_func(current_room)
            ]

    
    return player_action_options
    





def check_user_input_error(action_idx : str, action_options : list[str]) -> tuple[bool, str]:

    """Checks if the user's input is valid. If not: return (True, "error message"), otherwise: return (False, "")"""

    if not action_idx.isdigit():
        return (True, f"'{action_idx}' isn't a valid option")
    
    if not action_idx < len(action_options):
        return (True, f"'{action_idx}' is out of range")
    
    return (False, "")

def run_game():
    map : Map = Map(CONSTANTS["map_base_size"])
    player = Player(CONSTANTS["player_base_hp"], map.starting_position)

    Map.open_window(map)


    while True:
        action_options : list[str] = get_player_action_options(player, map)
        print("\n".join(f"{idx}) {action}" for idx,action in enumerate(action_options)))

        action_idx : str[int] = input("Choose action: ")
        err, err_message = check_user_input_error(action_idx, action_options)
        if err:
            print(err_message)
            continue

        
        match action_options[int(action_idx)]:
            case "Attack":
                pass

            case "Open inventory":
                pass
            
            case "Attempt to flee":
                pass
            
            case "Open chest":
                pass
            
            case _other: # all other cases, aka Open door ...
                assert _other.startswith("Open door facing")
                door_to_open = _other.rsplit(" ", 1)[-1] # gets all text before the last space
                
            



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