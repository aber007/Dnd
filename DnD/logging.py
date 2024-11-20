from . import CONSTANTS, INTERACTION_DATA, SKILL_TREE_DATA, ANSI, Bar, wait_for_key
from random import choice
import sys

def write(*s : str, sep="", end="\n") -> int:
    """Returns the amount of lines written to console"""

    text = sep.join(str(_s) for _s in s) + end
    sys.stdout.write(text)
    sys.stdout.flush()

    return len(text.split("\n"))




class Log:
    class Debug:
        def print_map(rooms, existing_walls):
            last_y = 0
            for x, y, walls in existing_walls:
                if y != last_y: print() ; last_y = y
                write(f" [{x},{y},{''.join([d for d,v in walls.items() if v == False])}] ".ljust(22, " "), end="")
            write("\n"*2)
            
            last_y = 0
            for x, y, room in rooms:
                if y != last_y: print() ; last_y = y
                write(f" [{x},{y},{room.type},{''.join(room.doors)}] ".ljust(22, " "), end="")
            write("\n")

    class CombatHistory:
        def __init__(self) -> None:
            pass
    
    def header(content : str, lvl : int) -> int:
        match lvl:
            case 1:
                return write(ANSI.clear_line, "="*15, f" {content} ", "="*15, end="\n"*2)
            
            case 2:
                return write(ANSI.clear_line, "-"*15, f") {content} (", "-"*15, end="\n"*2)
    
    def newline(count : int = 1) -> int:
        return write("\n"*count, end="")
    
    def clear_console():
        write(ANSI.clear_terminal, ANSI.Cursor.set_xy_0, end="")
    

    def clear_lines(n : int):
        """Clears the current line then moves up. Repeat this n times. The cursor is moved up 1 less time than n,\n
        which places the cursor at the beginning of the highest cleared line\n
        Eg. n = 2 : clear, move up, clear"""
        write(ANSI.Cursor.move_up.join([ANSI.clear_line]*n), end="")


    # game related
    def game_over(won : bool):
        if won:
            write("Congratulations! You escaped the castle or something")
        else:
            write("Game over")
    

    # item related
    def use_combat_item_outside_combat():
        write("You shouldn't use an offensive item outside of combat")
    
    def used_eye_of_horus(selected_direction : str, room_contains_text : str):
        write(f"The Eye of Horus shows you that the room behind the door facing {selected_direction} contains {room_contains_text}")
    
    def item_broke(item_name : str):
        write(f"{item_name} broke and is now useless!")
    
    def received_item(name_in_sentence : str, description : str):
        write(f"You recieved {name_in_sentence}", description, sep="\n")
    
    def received_item_inventory_full():
        write("Your inventory is full!")
    
    def item_thrown_out(item_name : str):
        write(f"{item_name} was thrown out")
    
    def list_inventory_items(items_in_inventory : list[any]) -> int:
        item_strings = [f"Slot {idx+1}) {item.name if item != None else ''}" for idx,item in enumerate(items_in_inventory)]
        return write(*item_strings, sep="\n")
    
    def inventory_empty() -> int:
        return write("You have no items to use!")


    # player related
    def player_healed(hp_before : int, additional_hp : int, hp_delta : int, current_hp : int):
        write(f"The player was healed for {additional_hp} HP{f' (capped at {hp_delta} HP)' if additional_hp != hp_delta else ''}. HP: {hp_before} -> {current_hp}")
    
    def player_max_hp_increased(previous_max_hp : int, current_max_hp : int):
        write(f"The player's max HP has increased! Max HP: {previous_max_hp} -> {current_max_hp}")
    
    def player_bonus_dmg_increased(previous_dmg_bonus : int, current_dmg_bonus : int):
        write(f"The player's dmg bonus has increased! Dmg bonus: {previous_dmg_bonus} -> {current_dmg_bonus}")
    
    def player_lvl_up(new_lvl : int, lvl_delta : int):
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
    
    def player_exp_til_next_lvl(exp : int):
        write(f"EXP til next lvl: {exp}")
    
    def list_player_stats(inventory : any) -> int:
        line_count = write(f"Gold: {inventory.gold}")

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
        line_count += 1

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
        line_count += 1

        line_count += write(f"Permanent DMG bonus: {inventory.parent.permanent_dmg_bonus}")
        return line_count

    def view_inventory(inventory : any, items_in_inventory : list[any]) -> int:
        line_count =  Log.header("INVENTORY", 1)
        line_count += Log.list_player_stats(inventory)
        line_count += Log.newline()
        line_count += Log.list_inventory_items(items_in_inventory)
        return line_count

    def view_skill_tree(player : any):
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
        line_count = 1
        line_count += write(*formatted_branch_strings, sep="\n"*2, end="\n"*2)

        wait_for_key("[Press ENTER to continue]", "enter")
        line_count += 1

        Log.clear_lines(line_count)


    # entity related
    def entity_took_dmg(entity_name : str, dmg : int, hp_remaining : int, is_alive : int, source : str = ""):
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

    def entity_received_effect(entity_name : str, effect_type : str, dmg : int, duration : int):
        write(f"The {entity_name} has been hit by a {effect_type} effect, dealing {dmg} DMG for {duration} rounds")
    
    def effect_tick(target_name : str, effect_type : str, dmg : int, duration : int):
        write(
            f"The {target_name} was hurt for {dmg} DMG from the {effect_type} effect.",
            (
                f"Duration remaining: {duration}" if duration != 0 else
                f"The {effect_type} effect wore off"
            )
            )
    

    # room related
    def first_time_enter_spawn_room():
        write(choice(INTERACTION_DATA["start"]))

    def entered_room(room_type : str):
        text_options = INTERACTION_DATA.get(room_type, None)
        if text_options != None:
            write(choice(text_options))
    
    def triggered_mimic_trap():
        write(choice(INTERACTION_DATA["mimic_trap"]))
    
    def stepped_in_trap(min_roll_to_escape : int):
        write(f"You stepped in a trap! Roll at least {min_roll_to_escape} to save yourself")
    
    def escaped_trap(roll : int, harmed : bool):
        write(f"You rolled {roll} and", ('managed to escape unharmed' if not harmed else 'was harmed by the trap while escaping'), sep=" ")

    def shop_display_current_gold(gold : int):
        write(f"Current gold: {gold}")
    
    def shop_insufficient_gold():
        write("You do not have enough gold to buy this item")
    
    def shop_out_of_stock():
        write("This shop is out of items")
