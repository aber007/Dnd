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
    INTERACTION_DATA,
    SKILL_TREE_DATA,
    Item,
    Inventory,
    Vector2,
    Array2D,
    get_user_action_choice,
    ensure_terminal_width,
    wait_for_key,
    Bar,
    RGB,
    CreateWallsAlgorithm,
    DodgeEnemyAttack,
    Effect
    )

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager



class Entity:
    def take_damage(self, dmg : int, dmg_type = "melee") -> int:
        if isinstance(self, Enemy) and dmg_type == "melee": dmg = max(0, dmg - self.defence_melee)
        elif isinstance(self, Player):                      dmg = max(0, dmg - self.defence); self.stats["hp lost"] += dmg
        
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
        self.max_hp = CONSTANTS["player_max_hp"]
        self.defence = CONSTANTS["player_base_defence"]
        self.current_combat : Combat | None = None

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
        self.hp = min(self.hp + additional_hp, self.max_hp)
        hp_delta = self.hp - hp_before
        print(f"The player was healed for {additional_hp} HP{f' (capped at {hp_delta} HP)' if additional_hp != hp_delta else ''}. HP: {hp_before} -> {self.hp}")

        self.stats["hp gained"] += hp_delta
    
    def on_lvl_up(self):
        """Set the players bonus health and dmg based on the current lvl"""

        # health
        previous_max_hp = self.max_hp
        self.max_hp = CONSTANTS["player_max_hp"] + math.floor(CONSTANTS["player_lvl_to_bonus_hp_func"](self.inventory.lvl))
        max_hp_delta = self.max_hp - previous_max_hp
        print(f"\nThe player's max HP has increased! Max HP: {previous_max_hp} -> {self.max_hp}")

        self.heal(max_hp_delta) # heal the player for the new max hp

        # dmg
        previous_dmg_bonus = self.permanent_dmg_bonus
        self.permanent_dmg_bonus = CONSTANTS["player_lvl_to_bonus_dmg_func"](self.inventory.lvl)
        print(f"The player's dmg bonus has increased! Dmg bonus: {previous_dmg_bonus} -> {self.permanent_dmg_bonus}")
    
    def _get_skill_tree_progression_options(self) -> tuple[list[int]]:
        branch_options_prefixes = []
        branch_options = []
        subtexts = []

        color_red = RGB(*CONSTANTS["skill_tree_cross_color"], "bg")
        color_green = RGB(*CONSTANTS["skill_tree_check_color"], "bg")
        color_off = CONSTANTS["color_off"]

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
                clear_console()
            
            print(f"{'='*15} SPEND SKILL POINTS {'='*15}", end="\n"*2)

            branch_options_prefixes, branch_options, subtexts = self._get_skill_tree_progression_options()
            branch_option_idx = get_user_action_choice("Choose branch to progress in: ", action_options=branch_options, action_options_prefixes=branch_options_prefixes, subtexts=subtexts)

            # "Special - Syphon" -> "Special", "Syphon"
            branch_name_w_colored_bars, skill_name = branch_options[branch_option_idx].split(" - ", 1)
            branch_name = branch_name_w_colored_bars.split(CONSTANTS["color_off"], 1)[0]
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

            if idx+1 != new_skill_points:
                wait_for_key("[Press ENTER to continue]", "enter")
    
    def call_skill_functions(self, when : str, variables : dict[str,any]) -> list[any]:
        return_vars = []
        for func in self.skill_functions[when]:
            return_vars.append( {"val": func(variables), "return_val_type": func.return_val_type} )
        
        return return_vars


        
class Enemy(Entity):
    def __init__(self, enemy_type : str, target : Player) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value won't be useful it's not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.is_alive = True
        self.active_effects = []
    
    def attack(self, target, dmg_multiplier : int = 1) -> int:
        """Attack target with base damage * dmg_multiplier. The damage dealt is returned"""
        return target.take_damage(math.ceil(self.dmg * dmg_multiplier))
    
    def use_special(self, special : str) -> None:
        """Runs the code for special abilities which can be used during combat"""
        pass

    def add_effect(self, type : str, effect : int, duration : int):
        self.active_effects.append(Effect(type=type, effect=effect, duration=duration, target=self))
        print(f"The {self.name} has been hit by a {type} effect, dealing {effect} DMG for {duration} rounds")
    
    def update_effects(self):
        # instance the self.active_effects list since effect.tick() might remove itself from the list
        for effect in list(self.active_effects):
            effect.tick()



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
                    music.play("fight")
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
                                if selected_item.current_price <= player.inventory.gold:
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

        # turn the Map.ReachableRoom objects into Map.Room object, inheriting the generated doors
        for x, y, _ in self.rooms:
            room_doors = self.get_doors_in_room(x,y)
            if (x, y) == self.starting_position:
                self.rooms[x,y] = Map.Room(type="empty", discovered=True, doors=room_doors)
            else:
                roomtype = choices(room_types, probabilities)[0]
                self.rooms[x,y] = Map.Room(type=roomtype, discovered=False, doors=room_doors)
        

        if CONSTANTS["debug"]["print_map"]:
            last_y = 0
            for x, y, walls in self.existing_walls:
                if y != last_y: print() ; last_y = y
                print(f" [{x},{y},{''.join([d for d,v in walls.items() if v == False])}] ".ljust(22, " "), end="")
            print("\n"*2)
            
            last_y = 0
            for x, y, room in self.rooms:
                if y != last_y: print() ; last_y = y
                print(f" [{x},{y},{room.type},{''.join(room.doors)}] ".ljust(22, " "), end="")
            print("\n")

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
                new_probability = distace_from_spawn/10 * ((100-ENEMY_DATA[enemy_type]["exp"])/1000 + ((player.inventory.get_lvl()**0.9)/100))
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

            self.enemy.update_effects()

            self.write_hp_bars()

            if not enemyturn:
                fled = self.player_turn()
            else:
                self.enemy_turn()
            
            sleep(1)
            enemyturn = not enemyturn
        
        # if the combat ended and the enemy died: mark the room as cleared
        if not self.enemy.is_alive:
            print(f"\n{'='*15} COMBAT COMPLETED {'='*15}\n")

            story_text_enemy_defeated = str(choice(INTERACTION_DATA["enemy_defeated"]))
            print(story_text_enemy_defeated.replace("enemy", self.enemy.name))
            print(f"You picked up {self.enemy.gold} gold from the {self.enemy.name}")
            print(f"You earned {self.enemy.exp} EXP from this fight\n")

            self.map.get_room(self.player.position).is_cleared = True

            self.player.inventory.gold += self.enemy.gold
            self.player.inventory.exp += self.enemy.exp
            self.player.inventory.update_lvl()

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
            fill_color=RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=player_bar_prefix
        )
        Bar(
            length=enemy_bar_length,
            val=self.enemy.hp,
            min_val=0,
            max_val=self.enemy.max_hp,
            fill_color=RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=enemy_bar_prefix
        )
        print()

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
            dmg += self.player.permanent_dmg_bonus

            dmg_mod = combat_bar()

            match dmg_mod:
                case "hit":
                    dmg_mod=1
                    print(f"\nThe {self.enemy.name} was hurt by the player using {item_name_in_sentence}")
                case "hit_x2":
                    dmg_mod=2
                    print(f"\nThe {self.enemy.name} was hurt by the player for 2x damage using {item_name_in_sentence}")
                case "miss":
                    print(f"\nYou missed the {self.enemy.name}")
                    action_completed = True
                    return action_completed

            # activate all the skills that are supposed to be ran before the attack fires
            return_vars = self.player.call_skill_functions(
                when="before_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg"])
            dmg = returned_dmg if len(return_vars) and returned_dmg != 0 else dmg

            dmg *= dmg_mod * self.player.temp_dmg_factor

            self.player.stats["dmg dealt"] += dmg

            if CONSTANTS["debug"]["player_infinite_dmg"]:
                dmg = 10**6

            dmg_dealt = self.enemy.take_damage(dmg)
            print(f"\nYou attacked the {self.enemy.name} for {dmg_dealt} damage")

            # activate all the skills that are supposed to be ran after the attack fires
            return_vars = self.player.call_skill_functions(
                when="after_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg_done = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg_done" and return_var["val"] != None])
            if 0 < returned_dmg_done:
                print(f"A skill of yours dealt {returned_dmg_done} damage to the {self.enemy.name}")

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
                    print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing")
                else:
                    print(f"The {self.enemy.name} managed to hit you for {dmg_dealt_to_player} while fleeing, killing you in the process")
            
            # if you escaped with coins
            elif CONSTANTS["flee_exact_roll_to_escape_coins"] <= roll:
                print(choice(INTERACTION_DATA["escape_20"]))
                self.player.inventory.gold += self.enemy.gold // CONSTANTS["flee_20_coins_to_receive_divider"]
                self.player.stats["gold earned"] += self.enemy.gold // CONSTANTS["flee_20_coins_to_receive_divider"]
            
            print(choice(INTERACTION_DATA["escape"]))
            fled = True

        # if you didnt escape
        else:
            dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=2)

            if self.player.is_alive:
                print(f"You failed to flee and took {dmg_dealt_to_player} damage")
            else:
                print(f"You failed to flee and took {dmg_dealt_to_player} damage, killing you in the process")
        
        return fled
    
    def enemy_turn(self):
        dmg_factor = DodgeEnemyAttack().start()
        dmg_dealt_to_player = self.enemy.attack(target=self.player, dmg_multiplier=dmg_factor)

        if self.player.is_alive:
            print(f"\nThe {self.enemy.name} attacked you for {dmg_dealt_to_player} damage")
        else:
            print(f"\nThe {self.enemy.name} attacked you for {dmg_dealt_to_player} damage, killing you in the process")
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

def clear_console():
    """Clears the entire console and sets cursor pos top left"""
    print("\033[2J" + "\033[H", end="")



def run_game():
    ensure_terminal_width(CONSTANTS["min_desired_terminal_width"])

    map = Map()
    player = Player(map)

    map.open_UI_window(player_pos = player.position)

    music = Music()

    while player.is_alive and player.inventory.lvl < 20:
        if not CONSTANTS["debug"]["disable_console_clearing"]:
            clear_console()
        
        print(f"{'='*15} NEW ROUND {'='*15}", end="\n"*2)

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

        wait_for_key("\n[Press ENTER to continue]\n", "enter")

    if not player.is_alive:
        print("\nGame over")
    
    else:
        print("\n" + "Congratulations! You escaped the castle or something.")

    # Shows lifetime stats
    print(f"\n{"="*15}")
    for key, values in player.stats.items():
        print(f"{key}: {values}")

    print(f"{"="*15}")

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
