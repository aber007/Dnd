CONSTANTS = {
    "map_base_size": (8,8),
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
        def __init__(self) -> None:
            pass
            self.content = ""
            self.doors = []
            #eg. self.content = "monster" / "chest" / "mimic" / None
            #eg. self.doors = ["north", "south", "west"]
            #given the above situation the player would be able to move north, south or west

    def __init__(self, size : tuple[int,int]) -> None:
        """Generates the playable map"""
        self.starting_position = (0,0)

    def open_window():
        """Opens the playable map in a separate window"""
        pass

    def get_room(x : int, y : int) -> Room:
        """Using an x and a y value, return a room at that position or None"""
        pass




def get_player_action_options(player : Player, map : Map) -> list[str]:
    """Returns a list of strings containing the different actions the player can currently take"""
    

    current_room : Map.Room = map.get_room(player.position)
    get_door_options_func = lambda current_room: [f"Open door facing {door_direction}" for door_direction in current_room.doors()]


    match current_room.content:
        case None:
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