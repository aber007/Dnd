import os, time
from random import randint, choices
from . import (
    CONSTANTS,
    ITEM_DATA,
    ROOM_DATA,
    openUIMap,
    Item,
    Lore,
    Music,
    Vector2,
    Array2D,
    get_user_action_choice,
    wait_for_key,
    CreateWallsAlgorithm,
    Log,
    Console,
    PlayerInputs,
    Player,
    Combat
    )

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager

class Map:

    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.horus_was_used : bool = False
            self.chest_item : Item | None = None
            self.enemy_type : str | None = None
            self.shop_items : list[Item] = []

            self.is_cleared : bool = False

        def on_enter(self, player : Player, map, first_time_entering_room : bool) -> None:
            """Called right when the player enters the room. E.g. starts the trap interaction or decides a chest's item etc"""

            # on_enter room log message
            if self.type == "enemy" and self.is_cleared:
                Log.entered_room("room_default")
            elif self.type == "mimic_trap":
                Log.entered_room("chest")
            else:
                Log.entered_room(self.type)

            # set music
            match self.type:
                case "shop":
                    Music.play("shop")
                
                case "enemy": 
                    if self.is_cleared:
                        Music.play("ambience")
                
                case _:
                    Music.play("ambience")


            # the enemy spawn, chest_item decision and shop decisions should only happen once
            # the non-mimic trap should always trigger its dialog
            match (self.type, first_time_entering_room):
                case ("enemy", True):
                    combat_instance = Combat(player, map)
                    self.enemy_type = combat_instance.enemy.name
                    combat_instance.start()
                    Log.clear_last_room_entered_text()
                
                case ("enemy", False):
                    if not self.is_cleared:
                        Combat(player, map, force_enemy_type=self.enemy_type).start()
                        Log.clear_last_room_entered_text()

                case ("chest", True):
                    possible_items = list(ITEM_DATA.keys())

                    if Lore.all_pages_discovered():
                        possible_items.remove("note")

                    item_probabilites = [ITEM_DATA[item_id]["probability"] for item_id in possible_items]
                    chosen_chest_item_id = choices(possible_items, item_probabilites)[0]

                    self.chest_item = Item(chosen_chest_item_id)

                case ("shop", True):
                    possible_items = list(ITEM_DATA.keys())

                    if Lore.all_pages_discovered():
                        possible_items.remove("note")

                    item_probabilites = [ITEM_DATA[item_id]["probability"] for item_id in possible_items]

                    shop_item_ids = choices(possible_items, item_probabilites, k=CONSTANTS["shop_item_count"])
                    for item_id in shop_item_ids:
                        item = Item(item_id)

                        min_price = round(item.base_price * -CONSTANTS["shop_item_price_range_factor"])
                        max_price = round(item.base_price * CONSTANTS["shop_item_price_range_factor"])
                        item.current_price = item.base_price + randint(min_price, max_price)
                        self.shop_items.append(item)

                case ("trap", _):
                    Log.stepped_in_trap(CONSTANTS["normal_trap_min_roll_to_escape"])
                    wait_for_key("[Press ENTER to roll dice]", "Return")
                    roll = player.roll_dice()

                    if CONSTANTS["normal_trap_min_roll_to_escape"] <= roll:
                        Log.escaped_trap(roll, False)
                    else:
                        Log.escaped_trap(roll, True)
                        Log.newline()
                        player.take_damage(CONSTANTS["normal_trap_dmg"])
                    
                    Log.newline()
                    wait_for_key("[Press ENTER to continue]", "Return")
                    Log.clear_last_room_entered_text()
            
            # update the tile the player just entered
            player.parent_map.UI_instance.send_command("tile", player.position, player.parent_map.decide_room_color(player.position))

        def interact(self, player : Player, map) -> None:
            """Called when the player chooses to interact with a room. E.g. opening a chest or opening a shop etc\n
            This is especially useful when dealing with the mimic trap as appears to be a chest room, thus tricking the player into interacting"""

            match self.type:
                case "chest":
                    player.inventory.receive_item(self.chest_item)
                    self.chest_item = None
                    self.is_cleared = True

                    Log.newline()
                    wait_for_key("[Press ENTER to continue]", "Return")

                case "mimic_trap":
                    Log.triggered_mimic_trap()
                    player.take_damage(CONSTANTS["mimic_trap_ambush_dmg"], source="Mimic ambush")

                    if player.is_alive:
                        Combat(player, map, force_enemy_type = "Mimic").start()
                    else:
                        Log.newline()
                        wait_for_key("[Press ENTER to continue]", "Return")

                case "shop":
                    Log.clear_console()
                    Log.header("SHOP", 1)
                    
                    
                    # stay in the shop menu until the player explicitly chooses to Leave
                    shop_option_idx = 0
                    while True:

                        Console.save_cursor_position("shop start")
                        Log.shop_display_current_gold(player.inventory.gold)
                        
                        shop_options = [f"{item}: {item.current_price} gold" for item in self.shop_items]
                        shop_options += ["Open Inventory", "Leave"]
                        shop_option_idx = get_user_action_choice("Choose item to buy: ", shop_options, start_y=shop_option_idx)

                        match shop_options[shop_option_idx]:
                            case "Open Inventory":
                                player.open_inventory()

                            case "Leave":
                                break

                            case _other:
                                # the player chose an item to buy
                                selected_item = self.shop_items[shop_option_idx]

                                # if the player can afford the item
                                if selected_item.current_price <= player.inventory.gold:
                                    player.inventory.gold -= selected_item.current_price
                                    player.inventory.receive_item(selected_item)
                                    self.shop_items.remove(selected_item)

                                else:
                                    Log.shop_insufficient_gold()
                                
                                Log.newline()
                                wait_for_key("[Press ENTER to continue]", "Return")
                                Console.truncate("shop start")
                                    
                        
                        if len(self.shop_items) == 0:
                            Log.shop_out_of_stock()
                            self.is_cleared = True
                            
                            Log.newline()
                            wait_for_key("[Press ENTER to continue]", "Return")
                            break
                        
                        Console.truncate("shop start")

            # update the tile the player just interacted with
            player.parent_map.UI_instance.send_command("tile", player.position, player.parent_map.decide_room_color(player.position))

    class UI:
        def __init__(self, size, rooms) -> None:
            # to be set by the parent Map object
            self.size : int = size
            self.rooms : Array2D[Map.Room] = rooms

            self.manager = Manager()
            self.command_queue = self.manager.Queue(maxsize=100)
            self.player_input_queue = self.manager.Queue()
            self.UI_thread : Process | None = None

            PlayerInputs.start_thread(self.player_input_queue)
        
        def open(self, player_pos : Vector2, existing_walls):
            self.UI_thread = Process(
                target=openUIMap,
                args=(
                    self.size,
                    self.rooms,
                    player_pos,
                    existing_walls,
                    self.command_queue,
                    self.player_input_queue
                ))
            self.UI_thread.start()
            time.sleep(1) # block the main thread til the UI thread tk window is open (self.UI_thread.is_alive() doesnt work here)
        
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

        if size % 2 == 0:
            size += 1
        self.size = size

        self.starting_position = Vector2(double=self.size//2)
        self.existing_walls : Array2D[dict[str,bool]] = CreateWallsAlgorithm(self.size, self.starting_position).start()
        room_types = list(ROOM_DATA["probabilities"].keys())
        probabilities = list(ROOM_DATA["probabilities"].values())

        # Initialize 2D array
        self.rooms : Array2D = Array2D.create_frame_by_size(width = self.size, height = self.size)

        # create a Map.Room object and assign its doors for each position the rooms Array2D
        for x, y, _ in self.rooms:
            room_doors = self.get_doors_in_room(x,y)
            if (x, y) == self.starting_position:
                self.rooms[x,y] = Map.Room(type="empty", discovered=True, doors=room_doors)
            else:
                roomtype = choices(room_types, probabilities)[0]
                self.rooms[x,y] = Map.Room(type=roomtype, discovered=False, doors=room_doors)
        

        if CONSTANTS["debug"]["print_map"]:
            Log.Debug.print_map()

        self.UI_instance = Map.UI(self.size, self.rooms)

    def get_doors_in_room(self, x, y) -> list[str]:
        room_doors = []

        if y > 0 and self.existing_walls[x, y-1]["S"] != True:
            room_doors.append("N")
        if x < self.size and self.existing_walls[x, y]["E"] != True:
            room_doors.append("E")
        if y < self.size and self.existing_walls[x, y]["S"] != True:
            room_doors.append("S")
        if x > 0 and self.existing_walls[x-1, y]["E"] != True:
            room_doors.append("W")

        return room_doors

    def open_UI_window(self, player_pos : Vector2) -> None:
        """Opens the playable map in a separate window"""

        # Press the map and then escape to close the window
        self.UI_instance.open(player_pos, self.existing_walls)

    def close_UI_window(self) -> None:
        self.UI_instance.close()

    def get_room(self, position : Vector2) -> Room:
        """Using an x and a y value, return a room at that position"""
        return self.rooms[position]

    def decide_room_color(self, room_position : Vector2) -> str:
        room : Map.Room = self.get_room(room_position)
        colors = ROOM_DATA["ui_colors"]

        match room.type:
            case "empty":
                return colors["discovered"] if room.discovered else colors["empty"]

            case "trap":
                return colors["trap"]

            case "mimic_trap":
                if    room.is_cleared: return colors["discovered"]
                elif  room.horus_was_used and not room.is_cleared: return colors[room.type]
                else: return colors["chest"]

            case _:
                return colors["discovered"] if room.is_cleared else colors[room.type]

    def move_player(self, direction : str, player : Player) -> None:
        """Move the player in the given direction"""

        player.position += CONSTANTS["directional_coord_offsets"][direction]
        new_current_room = self.get_room(player.position)

        first_time_entering_room = not new_current_room.discovered
        new_current_room.discovered = True
        
        self.UI_instance.send_command("tile", player.position, self.decide_room_color(player.position))
        self.UI_instance.send_command("pp", player.position)

        new_current_room.on_enter(player = player, map = self, first_time_entering_room = first_time_entering_room)
