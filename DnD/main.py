import os, math
from random import randint, choices, choice, uniform
from time import sleep
from .UI_map_creation import openUIMap
from .ambience import Music
from .terminal import combat_bar
from . import (
    CONSTANTS,
    ITEM_DATA,
    ENEMY_DATA,
    SKILL_TREE_DATA,
    Item,
    Inventory,
    Vector2,
    Array2D,
    get_user_action_choice,
    ensure_terminal_width,
    wait_for_key,
    Bar,
    ANSI,
    CreateWallsAlgorithm,
    DodgeEnemyAttack,
    Effect,
    Log,
    Console,
    Buff
    )

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager



class Entity:
    def take_damage(self, dmg : int, dmg_type : str = "melee", source : str = "", log : bool = True) -> int:
        """source is used to specify what caused the dmg. Only used if log == True"""
        if isinstance(self, Enemy) and dmg_type == "melee": dmg = max(0, dmg - self.defence_melee)
        elif isinstance(self, Player):                      dmg = max(0, dmg - self.defence); self.stats["hp lost"] += dmg
        
        self.hp = max(0, self.hp - dmg)
        self.is_alive = 0 < self.hp

        if log:
            Log.entity_took_dmg(self.name, dmg, self.hp, self.is_alive, source)
        
        return dmg
    
class MainMenu:
    
    def __init__(self, music : Music) -> None:
        self.music = music
        
    def start(self) -> bool:
        """Returns bool wether to start the game or not. If false then the user chose to quit the game"""

        user_wishes_to_start_game = False

        Log.header("MAIN MENU", 1)
        Console.save_cursor_position("main menu start")

        while True:
            action_options = ["Start Game", "Options", "Lore", "Help", "Quit Game"]
            action_idx = get_user_action_choice("", action_options)
            
            # remove the ItemSelect remains
            Console.truncate("main menu start")

            match action_options[action_idx]:
                case "Start Game":
                    user_wishes_to_start_game = True
                    break

                case "Options":
                    self.submenu_options()
                
                case "Lore":
                    """Shows lore (maybe remove? Are we lazy?)"""
                
                case "Help":
                    self.submenu_help()
                
                case "Quit Game":
                    break
            
            # remove the remains of eg. the options header
            Console.truncate("main menu start")
        
        return user_wishes_to_start_game

        # Print tip to guide users to Options later

    
    def submenu_options(self):
        Log.header("OPTIONS", 2)
        Console.save_cursor_position("options menu start")

        action_options = ["Music Volume", "Change Difficulty maybe?", "Add more shit later?", "Return"]
        action_idx = get_user_action_choice("", action_options)
        
        Console.truncate("options menu start")

        match action_options[action_idx]:
            case "Music Volume":
                self.music.change_volume()

            case "Change Difficulty maybe?":
                print("mimimi change difficulty")

            case "Add more shit later?":
                print("absolutely not.")
        
        # if theres text to display here use wait_for_key before the truncate call
        Console.truncate("options menu start")
    

    # build inside these
    def submenu_lore(self): ...
    def submenu_help(self):
        Log.header("Help", 2)
        print("\n Controls:\n Menu navigation - Up/Down-key\n Menu selection - Enter\n Slider controls - Left/Right-key\n")
        print(" The controls mentioned will not be usable\n outside of the game when playing.\n")
        Log.end()

        wait_for_key("Press Enter to go back", "enter")


class Player(Entity):
    def __init__(self, parent_map) -> None:
        self.parent_map : Map = parent_map
        self.position : Vector2 = self.parent_map.starting_position
        self.name = "player"

        # combat related attributes
        self.is_alive = True
        self.hp = CONSTANTS["player_hp"]
        self.max_hp = CONSTANTS["player_max_hp"]
        self.defence = CONSTANTS["player_base_defence"]
        self.current_combat : Combat | None = None
        self.active_effects = []

        self.permanent_dmg_bonus = 0
        self.temp_dmg_factor = 1

        # Fix this later, these are just temporary
        self.stats = {
            "hp gained": 0, # Fixed
            "hp lost": 0, # Fixed
            "gold earned": 0, # Fixed
            "exp gained": 0, # Fixed
            "dmg dealt": 0, # Fixed
            "monsters defeated": 0, # Fixed
        }

        # progression related attributes
        self.inventory = Inventory(parent=self)
        self.skill_tree_progression = {"Special": 0, "HP": 0, "DMG": 0}
        self.skill_functions = {"before_attack": [], "after_attack": [], "new_non_combat_round": []}

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
        """If any damage was dealt, return tuple[dmg, item name_in_sentence] or None"""

        selected_item : Item | None = self.inventory.open()

        if selected_item == None:
            return None

        if selected_item.offensive:
            if self.current_combat == None:
                Log.use_combat_item_outside_combat()
                Log.newline()
                wait_for_key("[Press ENTER to continue]", "enter")

            else:
                dmg = selected_item.use()
                return (dmg, selected_item.name_in_sentence)

        else:
            # non offensive items always return a callable where the argument 'player' is expected
            use_callable = selected_item.use()
            use_callable(self)

        return None

    def heal(self, additional_hp : int):
        # cap the hp to player_hp
        hp_before = self.hp
        self.hp = min(self.hp + additional_hp, self.max_hp)
        hp_delta = self.hp - hp_before

        Log.player_healed(hp_before, additional_hp, hp_delta, self.hp)
        self.stats["hp gained"] += hp_delta
    
    def on_lvl_up(self):
        """Set the players bonus health and dmg based on the current lvl"""

        # health
        previous_max_hp = self.max_hp
        self.max_hp += math.floor(CONSTANTS["player_lvl_to_bonus_hp_additive_func"](self.inventory.lvl))
        max_hp_delta = self.max_hp - previous_max_hp
        Log.player_max_hp_increased(previous_max_hp, self.max_hp)

        self.heal(max_hp_delta) # heal the player for the new max hp

        # dmg
        previous_dmg_bonus = self.permanent_dmg_bonus
        self.permanent_dmg_bonus += CONSTANTS["player_lvl_to_bonus_dmg_additive_func"](self.inventory.lvl)
        Log.player_bonus_dmg_increased(previous_dmg_bonus, self.permanent_dmg_bonus)
    
    def _get_skill_tree_progression_options(self) -> tuple[list[int]]:
        branch_options_prefixes = []
        branch_options = []
        subtexts = []

        color_red = ANSI.RGB(*CONSTANTS["skill_tree_cross_color"], "bg")
        color_green = ANSI.RGB(*CONSTANTS["skill_tree_check_color"], "bg")
        color_off = ANSI.Color.off

        # go through all branches and add them as an option if available
        for branch_name, stages in SKILL_TREE_DATA.items():
            # handle Impermanent perks separately
            if branch_name == "Impermanent": continue

            lvls_in_branch : int = len(stages)
            player_progression_in_branch : int = self.skill_tree_progression[branch_name]

            # if the branch isnt already completed
            if player_progression_in_branch + 1 <= lvls_in_branch:
                next_lvl_dict = stages[str(player_progression_in_branch+1)]

                # branch_progression_str is a comprised of a few colored boxes representing the players progression in this branch
                branch_progression_str = color_off + str(f"{color_green} {color_off}"*player_progression_in_branch) + str(f"{color_red} {color_off}"*(lvls_in_branch-player_progression_in_branch)) + color_off + " "

                branch_options_prefixes.append(branch_progression_str)
                branch_options.append(f"{branch_name} - {next_lvl_dict['name']}")
                subtexts.append(f"{' '*6}{next_lvl_dict['description']}")
        
        # add the Impermanent perks
        for branch_name, skill_dict in SKILL_TREE_DATA["Impermanent"].items():
            branch_options_prefixes.append("")
            branch_options.append(f"Impermanent - {skill_dict['name']}")
            subtexts.append(f"{' '*6}{skill_dict['description']}")
        
        return branch_options_prefixes, branch_options, subtexts

    def receive_skill_point(self, new_skill_points : int):
        wait_for_key(f"\nYou have {new_skill_points} unspent skill points!\n\n[Press ENTER to progress the skill tree]", "enter")

        for idx in range(new_skill_points):
            if not CONSTANTS["debug"]["disable_console_clearing"]:
                Log.clear_console()
            
            Log.header("SPEND SKILL POINTS", 1)

            branch_options_prefixes, branch_options, subtexts = self._get_skill_tree_progression_options()
            branch_option_idx = get_user_action_choice("Choose branch to progress in: ", action_options=branch_options, action_options_prefixes=branch_options_prefixes, subtexts=subtexts)

            # "Special - Syphon" -> "Special", "Syphon"
            branch_name_w_colored_bars, skill_name = branch_options[branch_option_idx].split(" - ", 1)
            branch_name = branch_name_w_colored_bars.split(ANSI.Color.off, 1)[0]
            match branch_name:
                case "Impermanent":
                    skill_name = skill_name.split(" ", 1)[0] # "HP boost" -> "HP"
                    skill_func = eval(SKILL_TREE_DATA[branch_name][skill_name]["func"])
                    skill_func({"player": self})

                case _:
                    branch_progression = self.skill_tree_progression[branch_name]
                    skill_dict = SKILL_TREE_DATA[branch_name][str(branch_progression+1)]
                    skill_func = eval(skill_dict["func"])
                    
                    if skill_dict["trigger_when"] == "now":
                        skill_func({"player": self})
                    else:
                        skill_func.return_val_type = skill_dict["return_val"]
                        self.skill_functions[skill_dict["trigger_when"]].append(skill_func)
                    
                    self.skill_tree_progression[branch_name] += 1
    
    def call_skill_functions(self, when : str, variables : dict[str,any]) -> list[any]:
        return_vars = []
        for func in self.skill_functions[when]:
            return_vars.append( {"val": func(variables), "return_val_type": func.return_val_type} )
        
        return return_vars
    
    def update_effects(self):
        # instance the self.active_effects list since effect.tick() might remove itself from the list
        for effect in list(self.active_effects):
            effect.tick()


        
class Enemy(Entity):
    def __init__(self, enemy_type : str, target : Player) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value won't be useful it's not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.is_alive = True
        self.active_effects = []
        self.active_buffs = []
        self.special_active = False
    
    def attack(self, target, dmg_multiplier : int = 1) -> int:
        """Attack target with base damage * dmg_multiplier. The damage dealt is returned"""
        return target.take_damage(math.ceil(self.dmg * dmg_multiplier), log=False)
    
    def use_special(self, special : str, player : Player) -> None:
        """Runs the code for special abilities which can be used during combat"""
        match special:
            case "trap":
                player.take_damage(player.defence + 2)
                print(f"You have been hit by a trap for 2 damage")
            case "berserk":
                self.active_buffs.append(Buff(type="dmg", effect=self.dmg, duration=5, target=self))
            case "poison":
                player.active_effects.append(Effect(type="poison", effect=2, duration=7, target=player))
            case "fire_breath":
                player.take_damage(ENEMY_DATA[self.name]["special_dmg"])
                print(f"You have been hit by fire breath for 8 damage")
            case "stone_skin":
                self.hp += (self.max_hp * 0.1)
                self.active_buffs.append(Buff(type="hp", effect=2, duration=2, target=self))
            

                

    def add_effect(self, type : str, effect : int, duration : int):
        self.active_effects.append(Effect(type=type, effect=effect, duration=duration, target=self))
        Log.entity_received_effect(self.name, type, effect, duration)
    
    def update_effects(self):
        # instance the self.active_effects list since effect.tick() might remove itself from the list
        for effect in list(self.active_effects):
            effect.tick()
        for effect in list(self.active_buffs):
            effect.tick()



class Map:

    class Room:

        def __init__(self, type, discovered, doors) -> None:
            self.type = type
            self.discovered = discovered
            self.doors = doors

            self.horus_was_used : bool = False
            self.chest_item : Item | None = None
            self.is_cleared : bool = False
            self.shop_items : list[Item] = []

        def on_enter(self, player : Player, map, first_time_entering_room : bool, music : Music) -> None:
            """Called right when the player enters the room. E.g. starts the trap interaction or decides a chest's item etc"""

            match self.type:
                case "shop":
                    music.play("shop")
                case "enemy": 
                    if not self.is_cleared: music.play("fight")
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

                case ("shop", True):
                    possible_items = list(ITEM_DATA.keys())
                    item_probabilites = [ITEM_DATA[item_id]["probability"] for item_id in possible_items]

                    shop_item_ids = choices(possible_items, item_probabilites, k=CONSTANTS["shop_item_count"])
                    for item_id in shop_item_ids:
                        item = Item(item_id)
                        item.current_price = item.base_price + randint(item.base_price // -CONSTANTS["shop_item_price_range_divider"], item.base_price // CONSTANTS["shop_item_price_range_divider"])
                        self.shop_items.append(item)

                case ("trap", _):
                    Log.stepped_in_trap(CONSTANTS["normal_trap_min_roll_to_escape"])
                    wait_for_key("[Press ENTER to roll dice]\n", "enter")
                    roll = player.roll_dice()

                    Log.newline()
                    if CONSTANTS["normal_trap_min_roll_to_escape"] <= roll:
                        Log.escaped_trap(roll, False)
                    else:
                        Log.escaped_trap(roll, True)
                        player.take_damage(CONSTANTS["normal_trap_dmg"])
                    
                    wait_for_key("[Press ENTER to continue]", "enter")
            
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

                    Log.newline()
                    wait_for_key("[Press ENTER to continue]", "enter")

                case "mimic_trap":
                    Log.triggered_mimic_trap()
                    player.take_damage(CONSTANTS["mimic_trap_ambush_dmg"], source="Mimic ambush")
                    music.play("fight")
                    Combat(player, map, force_enemy_type = "Mimic").start(music=music)

                case "shop":
                    Log.clear_console()
                    Log.header("SHOP", 1)
                    
                    
                    # stay in the shop menu until the player explicitly chooses to Leave
                    shop_option_idx = 0
                    while True:

                        Console.save_cursor_position("shop start")
                        Log.shop_display_current_gold(player.inventory.gold)
                        
                        shop_options = [f"{item.name}: {item.current_price} gold" for idx,item in enumerate(self.shop_items)]
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
                                wait_for_key("[Press ENTER to continue]", "enter")
                                Console.truncate("shop start")
                                    
                        
                        if len(self.shop_items) == 0:
                            Log.shop_out_of_stock()
                            self.is_cleared = True
                            
                            Log.newline()
                            wait_for_key("[Press ENTER to continue]", "enter")
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
            self.UI_thread : Process | None = None
        
        def open(self, player_pos : Vector2, existing_walls):
            self.UI_thread = Process(target=openUIMap, args=(self.size, self.rooms, player_pos, self.command_queue, existing_walls))
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

        if size % 2 == 0:
            size += 1
        self.size = size

        self.starting_position = Vector2(double=self.size//2)
        self.existing_walls : Array2D[dict[str,bool]] = CreateWallsAlgorithm(self.size, self.starting_position).start()
        room_types = list(CONSTANTS["room_probabilities"].keys())
        probabilities = list(CONSTANTS["room_probabilities"].values())

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
        colors = CONSTANTS["room_ui_colors"]

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
        self.enemy : Enemy = self.create_enemy(force_enemy_type, player)
        self.turn = 0

    def create_enemy(self, force_enemy_type : str | None, player) -> Enemy:
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
        for enemy_type in enemy_types:     
            if ENEMY_DATA[enemy_type]["probability"] == 0:
                last_probability = spawn_probabilities[enemy_type]
                new_probability = distace_from_spawn/10 * ((100-ENEMY_DATA[enemy_type]["exp"])/1000 + ((player.inventory.get_lvl()**0.9)/50))
                spawn_probabilities[enemy_type] += new_probability
            elif ENEMY_DATA[enemy_type]["probability"] > 0:
                last_probability = spawn_probabilities[enemy_type]
                new_probability = distace_from_spawn/10 * ((100-ENEMY_DATA[enemy_type]["exp"])/1000 + ((player.inventory.get_lvl()**0.9)/20))
                spawn_probabilities[enemy_type] -= new_probability
            if CONSTANTS["debug"]["show_enemy_probabilities"] and ENEMY_DATA[enemy_type]["probability"] >= 0:
                print(str(ENEMY_DATA[enemy_type]["name"]) + ": " + str(round(spawn_probabilities[enemy_type], 5)) + " : " + str(round(spawn_probabilities[enemy_type]-last_probability, 5))) #Not using fstring because of formatting issues
            
        
            


        enemy_type_to_spawn = choices(list(spawn_probabilities.keys()), list(spawn_probabilities.values()))[0]

        return Enemy(enemy_type = enemy_type_to_spawn, target = self.player)

    def start(self, music : Music) -> None:
        self.player.current_combat = self

        Log.combat_enemy_revealed(self.enemy.name_in_sentence)
        Log.newline()
        wait_for_key("[Press ENTER to continue]", "enter")
        Log.clear_console()
        Log.header("COMBAT", 1)
        
        enemyturn = choice([True, False])

        
        fled = False
        while self.player.is_alive and self.enemy.is_alive and not fled:
            self.turn += 1

            Console.save_cursor_position("combat round start")

            if self.turn == 1: sleep(1)
            Log.header(f"Turn {self.turn}", 2)

            self.enemy.update_effects()
            self.player.update_effects()

            self.write_hp_bars()

            if not enemyturn:
                fled = self.player_turn()
            else:
                self.enemy_turn()

            Log.newline()
            wait_for_key("[Press ENTER to continue]", "enter")
            Console.truncate("combat round start")
            
            enemyturn = not enemyturn
        
        # if the combat ended and the enemy died: mark the room as cleared
        if not self.enemy.is_alive:
            Log.clear_console()
            Log.header("COMBAT COMPLETED", 1)
            Log.enemy_defeated(self.enemy.name, self.enemy.gold, self.enemy.exp)

            self.map.get_room(self.player.position).is_cleared = True

            self.player.inventory.gold += self.enemy.gold
            self.player.inventory.exp += self.enemy.exp

            # if the player lvld up .update_lvl() would call wait_for_key
            # if the player didnt lvl up then call wait_for_key here
            Log.newline()
            player_lvld_up = self.player.inventory.update_lvl()

            if not player_lvld_up:
                Log.newline()
                wait_for_key("[Press ENTER to continue]", "enter")

            self.player.stats["gold earned"] += self.enemy.gold
            self.player.stats["exp gained"] += self.enemy.exp
            self.player.stats["monsters defeated"] += 1
            

        self.player.temp_dmg_factor = CONSTANTS["player_default_temp_dmg_factor"]
        self.player.current_combat = None
        music.play("ambience")

    def write_hp_bars(self):
        # Figure out which prefix is longer then make sure the shorter one gets padding to compensate
        enemy_bar_prefix = f"{self.enemy.name} hp: {self.enemy.hp}   "
        player_bar_prefix = f"Player hp: {self.player.hp}   "
        longer_prefix = sorted([enemy_bar_prefix, player_bar_prefix], key=lambda i : len(i), reverse=True)[0]

        enemy_bar_prefix = enemy_bar_prefix.ljust(len(longer_prefix), " ")
        player_bar_prefix = player_bar_prefix.ljust(len(longer_prefix), " ")

        # Make sure the side with more hp has the longest health bar allowed
        #   and that the side with less hp has a health bar proportionate to the hp ratio
        #   eg. player hp 10, enemy hp 1 -> player bar length = max, enemy bar length = max * 0.1
        max_hp_ratio = self.enemy.max_hp / self.player.max_hp
        if max_hp_ratio <= 1:
            # player has more hp or equal
            player_bar_length = CONSTANTS["hp_bar_max_length"]
            enemy_bar_length = round(CONSTANTS["hp_bar_max_length"] * max_hp_ratio)
        else:
            enemy_bar_length = CONSTANTS["hp_bar_max_length"]
            player_bar_length = round(CONSTANTS["hp_bar_max_length"] * max_hp_ratio)

        # Write the health bars to terminal
        Bar(
            length=player_bar_length,
            val=self.player.hp,
            min_val=0,
            max_val=self.player.max_hp,
            fill_color=ANSI.RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=player_bar_prefix
        )
        Bar(
            length=enemy_bar_length,
            val=self.enemy.hp,
            min_val=0,
            max_val=self.enemy.max_hp,
            fill_color=ANSI.RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=enemy_bar_prefix
        )
        Log.newline()

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
                    if action_completed:
                        break # skip Log.clear_lines

                case "Attempt to Flee":
                    return self.player_attempt_to_flee()
        
        return fled

    def player_use_item_attack(self) -> bool:
        """Returns wether the player sucessfully used an item or not, aka action_completed"""
        action_completed = False

        # item_return is either tuple[dmg done, item name_in_sentence] or None, depending on if any damage was done
        item_return = self.player.open_inventory()
        if item_return is not None:
            dmg, item_name_in_sentence = item_return
            dmg += self.player.permanent_dmg_bonus

            dmg_mod = combat_bar()
            dmg_factor = {"miss": 0, "hit": 1, "hit_x2": 2}[dmg_mod]

            Log.combat_player_attack_mod(dmg_factor, self.enemy.name, item_name_in_sentence)
            Log.newline()

            # if the player missed the enemy mark this turn as completed
            if dmg_factor == 0:
                return True

            # activate all the skills that are supposed to be ran before the attack fires
            return_vars = self.player.call_skill_functions(
                when="before_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg"])
            dmg = returned_dmg if len(return_vars) and returned_dmg != 0 else dmg

            dmg *= dmg_factor * self.player.temp_dmg_factor

            self.player.stats["dmg dealt"] += dmg

            if CONSTANTS["debug"]["player_infinite_dmg"]:
                dmg = 10**6

            self.enemy.take_damage(dmg)

            # activate all the skills that are supposed to be ran after the attack fires
            return_vars = self.player.call_skill_functions(
                when="after_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg_done = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg_done" and return_var["val"] != None])
            if 0 < returned_dmg_done:
                Log.newline()
                Log.player_skill_damaged_enemy(self.enemy.name, returned_dmg_done)

            action_completed = True
        
        return action_completed

    def player_attempt_to_flee(self) -> bool:
        """Returns wether the attempt to flee was successful"""
        fled = False
        
        Log.combat_init_flee_roll()

        wait_for_key("[Press ENTER to roll dice]", "enter")
        roll = self.player.roll_dice()
        
        Log.clear_line()
        Log.combat_flee_roll_results(roll)
        Log.newline()

        # if you managed to escape
        if CONSTANTS["flee_min_roll_to_escape"] <= roll:
            # if the enemy hit you on your way out
            if roll < CONSTANTS["flee_min_roll_to_escape_unharmed"]:
                dmg_dealt_to_player = self.enemy.attack(target=self.player)
                Log.enemy_attack_while_fleeing(self.enemy.name, dmg_dealt_to_player)
                Log.entity_took_dmg(self.player.name, dmg_dealt_to_player, self.player.hp, self.player.is_alive)
            
            # if you escaped with coins
            elif CONSTANTS["flee_exact_roll_to_escape_coins"] <= roll:
                Log.combat_perfect_flee()
                self.player.inventory.gold += self.enemy.gold // CONSTANTS["flee_20_coins_to_receive_divider"]
                self.player.stats["gold earned"] += self.enemy.gold // CONSTANTS["flee_20_coins_to_receive_divider"]
            
            Log.combat_flee_successful()
            fled = True

        # if you didnt escape
        else:
            dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=2)
            Log.enemy_attack_unsuccessful_flee(dmg_dealt_to_player)
            Log.entity_took_dmg(self.player.name, dmg_dealt_to_player, self.player.hp, self.player.is_alive)
        
        return fled
    
    def enemy_turn(self):
        dmg_factor = DodgeEnemyAttack().start()
        dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=dmg_factor)

        Log.newline()
        Log.enemy_attack(self.enemy.name, dmg_dealt_to_player)
        Log.entity_took_dmg(self.player.name, dmg_dealt_to_player, self.player.hp, self.player.is_alive)
        
        if self.player.is_alive and uniform(0, 1) < self.enemy.special_chance:
            Log.newline()
            print(self.enemy.special_info)
            self.enemy.use_special(self.enemy.special, player=self.player)

            # *player takes dmg from the special*



def get_player_action_options(player : Player, map : Map) -> list[str]:
    """Returns a list of strings containing the different actions the player can currently take"""

    current_room : Map.Room = map.get_room(player.position)
    door_options = [f"Open door facing {door_direction}" for door_direction in current_room.doors]

    default_action_options = [*door_options, "Open Inventory"]


    match current_room.type:
        case "empty":
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
    Console.clear()

    # ensures ItemSelect and music volume slider work properly, therefore must be first
    ensure_terminal_width(CONSTANTS["min_desired_terminal_width"])

    music = Music()

    # open main menu
    user_wishes_to_start_game = MainMenu(music).start()
    if not user_wishes_to_start_game:
        Log.write("Exiting game...")
        return

    # init the game
    map = Map()
    player = Player(map)

    map.open_UI_window(player_pos = player.position)

    game_just_started = True
    while player.is_alive and player.inventory.lvl < 20:
        if not CONSTANTS["debug"]["disable_console_clearing"]:
            Log.clear_console()
        
        Log.header("NEW ROUND", 1)
        
        
        if game_just_started:
            Log.first_time_enter_spawn_room()
            game_just_started = False
        else:
            Log.entered_room(map.get_room(player.position).type if map.get_room(player.position).type != "mimic_trap" else "chest")

        # activate all the skills that are supposed to be ran right when a new non-combat round starts
        player.call_skill_functions(
                when="new_non_combat_round",
                variables={"player": player}
                )

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
                door_to_open = _other.rsplit(" ", 1)[-1] # _other = "Open door facing N" -> door_to_open = "N"
                map.move_player(direction=door_to_open, player=player, music=music)


    Log.game_over(player.is_alive)


    # Shows lifetime stats
    Log.newline()
    Log.header("GAME STATS", 1)
    for key, values in player.stats.items():
        print(f"{key}: {values}")

    Log.newline()


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
