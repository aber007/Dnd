from . import (
    CONSTANTS,
    Music,
    get_user_action_choice,
    ensure_terminal_width,
    wait_for_key,
    MainMenu,
    Log,
    Console,
    PlayerInputs,
    Player,
    Map
    )
from random import uniform

def get_player_action_options(player : Player, map : Map) -> list[str]:
    """Returns a list of strings containing the different actions the player can currently take"""

    current_room : Map.Room = map.get_room(player.position)
    door_options = [f"Open door facing {door_direction}" for door_direction in current_room.doors]

    default_action_options = [*door_options, "Open Inventory"]

    match current_room.type, current_room.is_cleared:
        case ("chest" | "mimic_trap", False):
            player_action_options = [
                "Open chest",
                *door_options,
                "Open Inventory",
            ]
        
        case ("shop", False):
            player_action_options = [
                "Buy from shop",
                "Open Inventory",
                *door_options,
            ]
        
        case (_, _):
            player_action_options = default_action_options

    player_action_options.append("Main Menu")
    return player_action_options




def run_game():
    try:
        Console.clear()
        
        # ensures ItemSelect and music volume slider work properly, therefore must be first
        ensure_terminal_width(CONSTANTS["min_desired_terminal_width"])

        map : Map = Map()
        player = Player(map)

        # since the player inputs are captured using the tkinter window, init it before main menu
        map.open_UI_window(player_pos = player.position)

        # open main menu and get difficulty
        difficulty = MainMenu(game_started=False).start()
        

        # init the game

        # if the player didnt do a 'game action', eg. opened main menu or
        #    opened and closed their inventory: dont call skill functions and
        #    write the same 'entered room' message as last round
        supress_new_round = False
        game_just_started = True

        # setup the version of MainMenu to display for the user during the game
        in_game_menu = MainMenu(game_started=True)

        while player.is_alive:

            all_rooms_discovered : list[bool] = []
            all_rooms_discovered_status = False
            for x in range(map.size):
                for y in range(map.size):
                    room = map.rooms[x, y]
                    all_rooms_discovered.append(room.discovered)
            
            if difficulty == "escape":
                if False not in all_rooms_discovered:
                    all_rooms_discovered_status = True
                    break

            elif difficulty == "lvl":
                if player.inventory.lvl >= 10:
                    all_rooms_discovered_status = False
                    break
                elif False not in all_rooms_discovered:
                    all_rooms_discovered_status = True
                    break

                
            Log.clear_console()
            Log.header("NEW ROUND", 1)

            if game_just_started:
                Log.first_time_enter_spawn_room()
                game_just_started = False
            
            else:
                # in enter_room the text gets written to console and set to an attribute,
                # at the beginning of the next round (right now) write the text to console
                Log.recall_last_room_entered_text()

            # activate all the skills that are supposed to be ran right when a new non-combat round starts BUT only if suppress_new_round is false
            if not supress_new_round: player.call_skill_functions(when="new_non_combat_round", variables={"player": player})
            else: supress_new_round = False

            # Get a list of the players currently available options and ask user to choose
            action_options : list[str] = get_player_action_options(player, map)
            action_idx = get_user_action_choice("Choose action: ", action_options)

            # Decide what to do based on the player's choice
            match action_options[action_idx]:
                case "Open chest" | "Buy from shop":
                    # interact with the current room
                    map.get_room(player.position).interact(player, map)

                case "Open Inventory":
                    player.open_inventory()
                    supress_new_round = True

                case "Main Menu":
                    in_game_menu.start()
                    supress_new_round = True

                case _other: # all other cases, aka Open door ...
                    assert _other.startswith("Open door facing")
                    door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing N" -> door_to_open = "N"
                    map.move_player(direction=door_to_open, player=player)

        # Shows lifetime stats
        Music.play("ambience")

        Console.clear()
        if not all_rooms_discovered_status:
            Log.header("GAME WON" if player.is_alive else "GAME OVER", 1)
        else:
            Log.header("CASTLE ESCAPED", 1)
            Log.write("You managed to escape the castle and you are free from the contract")
        Log.game_over(player.is_alive)
        Log.newline()

        Log.header("GAME STATS", 2)
        Log.show_game_stats(player.stats)
        Log.newline()

        wait_for_key("[Press ENTER to close game]", "Return")
        raise SystemExit
    
    except SystemExit:
        Console.clear(final=True)
        PlayerInputs.kill_thread()
        map.close_UI_window()

    



if __name__ == "__main__":
    run_game()


# DO NOT REMOVE, IT'S NECESSARY

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
