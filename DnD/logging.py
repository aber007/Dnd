# This file is dedicated to unique logging functions used in a variety of scenarios in the game
# These comments exist to clarify the difference between terminal.py, logger.py and console_io.py

from . import CONSTANTS, INTERACTION_DATA, SKILL_TREE_DATA, ANSI, Bar, wait_for_key, Console
from random import choice


def write(*s : str, sep="", end="\n") -> int:
    """Similar to print() except using custom default variables\n
    Also returns the amount of line count written to console"""
    return Console.write(*s, sep=sep, end=end)



class _Log:

    class Debug:
        def print_map(rooms, existing_walls):
            last_y = 0
            for x, y, walls in existing_walls:
                if y != last_y: Log.newline() ; last_y = y
                write(f" [{x},{y},{''.join([d for d,v in walls.items() if v == False])}] ".ljust(22, " "), end="")
            write("\n"*2)
            
            last_y = 0
            for x, y, room in rooms:
                if y != last_y: Log.newline() ; last_y = y
                write(f" [{x},{y},{room.type},{''.join(room.doors)}] ".ljust(22, " "), end="")
            write("\n")
    
    def __init__(self) -> None:
        self.auto_flush = True
        

    def flush(_):
        """Flushes the content written to log into terminal"""
        Console.flush()

    
    def write(self, *s : str, sep : str = "", end : str = "\n") -> int:
        """Wrapper class for write. This allows other files to use write while only needing to import Log"""
        Console.write(*s, sep="", end="\n")

    def header(_, content : str, lvl : int) -> int:
        underline_str = ANSI.Text.double_underline if lvl == 1 else ANSI.Text.single_underline if lvl == 2 else ""

        length_left = (CONSTANTS["header_length"]-len(content)) // 2
        length_right = length_left + 1 if len(content) % 2 == 0 else length_left
        match lvl:
            case 1:
                return write(ANSI.clear_line, "="*length_left, f" {underline_str}{content}{ANSI.Text.off} ", "="*length_right, end="\n"*2)
            
            case 2:
                return write(ANSI.clear_line, "-"*(length_left-1), f") {underline_str}{content}{ANSI.Text.off} (", "-"*(length_right-1), end="\n"*2)
            
    def end(_):
        length = CONSTANTS["header_length"] + 2
        return write(ANSI.clear_line, "="*length, end="\n"*2) 
    
    def newline(_, count : int = 1) -> int:
        return write("\n"*count, end="")
    
    def clear_console(_):
        Console.clear()

    def clear_line(_):
        write(ANSI.clear_line, end="")

    def clear_lines(_, n : int):
        """Clears the current line then moves up. Repeat this n times. The cursor is moved up 1 less time than n,\n
        which places the cursor at the beginning of the highest cleared line\n
        Eg. n = 2 : clear, move up, clear"""
        write(*[ANSI.clear_line]*n, sep=ANSI.Cursor.move_up, end="")


    # game related
    def game_over(_, won : bool):
        if won:
            write("Congratulations! You escaped the castle or something")
        else:
            write("Game over")
    

    # item related
    def use_combat_item_outside_combat(_, ) -> int:
        return write("You shouldn't use an offensive item outside of combat")
    
    def used_eye_of_horus(_, selected_direction : str, room_contains_text : str):
        write(f"The Eye of Horus shows you that the room behind the door facing {selected_direction} contains {room_contains_text}")
    
    def item_broke(_, item_name : str):
        write(f"{item_name} broke and is now useless!")
    
    def received_item(_, name_in_sentence : str, description : str):
        write(f"You recieved {name_in_sentence}", description, sep="\n")
    
    def received_item_inventory_full(_):
        write("Your inventory is full!")
    
    def item_thrown_out(_, item_name : str):
        write(f"{item_name} was thrown out")
    
    def list_inventory_items(_, items_in_inventory : list[any]) -> int:
        item_strings = [f"Slot {idx+1}) {item.name if item != None else ''}" for idx,item in enumerate(items_in_inventory)]
        return write(*item_strings, sep="\n")
    
    def inventory_empty(_, ) -> int:
        return write("You have no items to use!")


    # player related    
    def player_max_hp_increased(_, previous_max_hp : int, current_max_hp : int):
        write(f"The player's max HP has increased! Max HP: {previous_max_hp} -> {current_max_hp}")
    
    def player_bonus_dmg_increased(_, previous_dmg_bonus : int, current_dmg_bonus : int):
        write(f"The player's dmg bonus has increased! Dmg bonus: {previous_dmg_bonus} -> {current_dmg_bonus}")
    
    def player_lvl_up(_, new_lvl : int, lvl_delta : int):
        if 0 < lvl_delta:
            write(
                (
                    f"{lvl_delta}x " if 1 < lvl_delta else
                    ""
                ),
                f"Level Up! Player is now level {new_lvl}",
            )
        else:
            write(f"Current lvl: {new_lvl}")
    
    def player_exp_til_next_lvl(_, exp : int):
        write(f"EXP til next lvl: {exp}")
    
    def list_player_stats(_, inventory : any):
        write(f"Gold: {inventory.gold}")

        exp_bar_prefix = f"Player Lvl: {inventory.lvl}, EXP: {inventory.exp}   "
        hp_bar_prefix = f"Player HP: {inventory.parent.hp}   "
        longer_prefix = sorted([exp_bar_prefix, hp_bar_prefix], key=lambda i : len(i), reverse=True)[0]

        exp_bar_prefix = exp_bar_prefix.ljust(len(longer_prefix), " ")
        hp_bar_prefix = hp_bar_prefix.ljust(len(longer_prefix), " ")

        min_val_min_width = max(len(str(inventory.parent.hp)), len(str(inventory.exp)))

        # hp bar
        Bar(
            length=CONSTANTS["hp_bar_max_length"],
            val=inventory.parent.hp,
            min_val=0,
            min_val_min_width=min_val_min_width,
            max_val=inventory.parent.max_hp,
            fill_color=ANSI.RGB(*CONSTANTS["hp_bar_fill_color"], "bg"),
            prefix=hp_bar_prefix
        )


        # exp bar
        Bar(
            length=CONSTANTS["exp_bar_max_length"],
            val=inventory.exp,
            min_val=CONSTANTS["player_lvl_to_exp_func"](inventory.lvl), # min exp for current lvl
            min_val_min_width=min_val_min_width,
            max_val=CONSTANTS["player_lvl_to_exp_func"](inventory.lvl+1), # min exp for next lvl
            fill_color=ANSI.RGB(*CONSTANTS["exp_bar_fill_color"], "bg"),
            prefix=exp_bar_prefix
        )

        write(f"Permanent DMG bonus: {inventory.parent.permanent_dmg_bonus}")

    def view_inventory(_, inventory : any, items_in_inventory : list[any]):
        Log.header("INVENTORY", 1)
        Log.list_player_stats(inventory)
        Log.newline()
        Log.list_inventory_items(items_in_inventory)

    def view_skill_tree(_, player : any):
        check_color = ANSI.RGB(*CONSTANTS["skill_tree_check_color"], "fg")
        check_str = f"{check_color}✔{ANSI.Color.off}"
        cross_color = ANSI.RGB(*CONSTANTS["skill_tree_cross_color"], "fg")
        cross_str = f"{cross_color}✖{ANSI.Color.off}"

        formatted_branch_strings = []

        for branch_name, branch_dict in SKILL_TREE_DATA.items():
            # dont show the Impermanent branch
            if branch_name == "Impermanent": continue

            branch_string_parts = [branch_name]

            for lvl_nr_str, lvl_dict in branch_dict.items():
                lvl_achieved = int(lvl_nr_str) <= player.skill_tree_progression[branch_name]

                if lvl_achieved:
                    lvl_str = f"{check_str} {lvl_dict['name']}: {lvl_dict['description']}"
                else:
                    lvl_str = f"{cross_str} ???: ???"
                branch_string_parts.append(lvl_str)
            
            formatted_branch_strings.append("\n".join(branch_string_parts))
        
        Log.header("SKILL TREE", 1)
        write(*formatted_branch_strings, sep="\n"*2, end="\n"*2)

        wait_for_key("[Press ENTER to continue]", "Return")


    # entity related
    def entity_took_dmg(_, entity_name : str, dmg : int, hp_remaining : int, is_alive : int, source : str = ""):
        entity_pronoun = "you" if entity_name == "player" else "it"
        write(
            f"The {entity_name} took {dmg} damage",
            (
                f" from the {source}" if source != "" else ""
            ),
            (
                f". {hp_remaining} HP remaining" if is_alive else
                f", killing {entity_pronoun} in the process"
            )
            )

    def entity_healed(_, entity_name, hp_before : int, additional_hp : int, hp_delta : int, current_hp : int):
        write(
            f"The {entity_name} was healed for {additional_hp} HP",
            (
                f" (capped at {hp_delta} HP). " if additional_hp != hp_delta else
                ". "
            ),
            f"HP: {hp_before} -> {current_hp}"
            )

    def entity_received_effect(_, effect_instance):
        action_str = {"hp": "healing", "dmg": "dealing"}[effect_instance.type]
        effect_suffix_str = effect_instance.type.upper()

        write(f"The {effect_instance.target.name} has been hit by a {effect_instance.name} effect, {action_str} {effect_instance.effect} {effect_suffix_str} for {effect_instance.duration} rounds")
    
    def effect_tick(_, effect_instance):
        action_str = {"hp": "healed", "dmg": "damaged"}[effect_instance.type]
        effect_suffix_str = effect_instance.type.upper()

        write(
            f"The {effect_instance.target.name} was {action_str} for {effect_instance.effect} {effect_suffix_str} from the {effect_instance.name} effect.",
            (
                f"Duration remaining: {effect_instance.duration}" if effect_instance.duration != 0 else
                f"The {effect_instance.name} effect wore off"
            ),
            sep=" ")

    # room related
    def first_time_enter_spawn_room(_) -> str:
        """Returns the text choice if this needs to be saved"""
        text_choice = choice(INTERACTION_DATA["start"])
        write(text_choice)
        return text_choice

    def entered_room(_, room_type : str) -> str:
        """Returns the text choice if this needs to be saved"""
        text_options = INTERACTION_DATA.get(room_type, None)
        if text_options != None:
            text_choice = choice(text_options)
            write(text_choice)
            return text_choice
    
    def triggered_mimic_trap(_):
        write(choice(INTERACTION_DATA["mimic_trap"]))
    
    def stepped_in_trap(_, min_roll_to_escape : int):
        write(f"You stepped in a trap! Roll at least {min_roll_to_escape} to save yourself")
    
    def escaped_trap(_, roll : int, harmed : bool):
        write(f"{ANSI.clear_line}You rolled {roll} and", ('managed to escape unharmed' if not harmed else 'was harmed by the trap while escaping'), sep=" ")

    def shop_display_current_gold(_, gold : int) -> int:
        return write(f"Current gold: {gold}")
    
    def shop_insufficient_gold(_, ) -> int:
        return write("You do not have enough gold to buy this item")
    
    def shop_out_of_stock(_):
        write("This shop is out of items")


    # combat related
    def combat_started(_, enemy_name_in_sentence : str):
        story_text_enemy = choice(INTERACTION_DATA["enemy"])
        if "enemy" in story_text_enemy:
            write(story_text_enemy.replace("enemy", enemy_name_in_sentence))
        else:
            write(story_text_enemy, f"An enemy appeared! It's {enemy_name_in_sentence}!", sep="\n"*2)
    
    def enemy_defeated(_, enemy_name : str, enemy_gold : int, enemy_exp : int):
        story_text_enemy_defeated = choice(INTERACTION_DATA["enemy_defeated"])
        write(
            story_text_enemy_defeated.replace("enemy", enemy_name),
            f"You picked up {enemy_gold} gold from the {enemy_name}",
            f"You earned {enemy_exp} EXP from this fight",
            sep="\n"
            )
    
    def enemy_attack(_, enemy_name : str, dmg : int):
        write(f"The {enemy_name} attacked you for {dmg} damage")
    
    def enemy_attack_while_fleeing(_, enemy_name : str, dmg : int):
        write(f"The {enemy_name} managed to hit you for {dmg} damage while fleeing")
    
    def enemy_attack_unsuccessful_flee(_, dmg : int):
        write(f"You failed to flee and took {dmg} damage")

    def combat_perfect_flee(_):
        write(choice(INTERACTION_DATA["escape_20"]))
    
    def combat_flee_successful(_):
        write(choice(INTERACTION_DATA["escape"]))
    
    def combat_init_flee_roll(_):
        write(f"Attempting to flee, Roll {CONSTANTS['flee_min_roll_to_escape']} or higher to succeed")

    def combat_flee_roll_results(_, roll : int):
        write(f"You rolled {roll}")
    
    def combat_player_attack_mod(_, success : int, enemy_name : str, item_name_in_sentence : str):
        if success == 0:
            write(f"You missed the {enemy_name}")
        else:
            write(
                f"The {enemy_name} was hurt by the player",
                (
                    " for 2x damage " if success == 2 else
                    " "
                ),
                f"using {item_name_in_sentence}"
                )
    
    def combat_enemy_revealed(_, enemy_name_in_sentence : str):
        enemy_name_in_sentence = enemy_name_in_sentence[0].upper() + enemy_name_in_sentence[1:]
        write(f"{enemy_name_in_sentence} appeared!")
    
    def player_skill_damaged_enemy(_, enemy_name : str, dmg : int):
        write(f"A skill of yours dealt {dmg} damage to the {enemy_name}")
    
    def enemy_used_special(_, special_info : str):
        write(special_info)


    # lore related
    def found_lore_letter_page(_, idx : str):
        write(f"You found page {int(idx)+1}")
    
    def found_irrelevant_lore_letter_page(_):
        write(f"The letter this page belonged to seems irrelevant")
    
    def write_lore_pages(_, pages : list[str]):
        write(*pages, sep="\n"*2)

Log = _Log()