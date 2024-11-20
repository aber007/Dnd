from . import INTERACTION_DATA
from random import choice
import sys

def write(*s : str, sep="", end="\n") -> None:
    sys.stdout.write(sep.join(str(_s) for _s in s) + end)
    sys.stdout.flush()

class Log:
    class CombatHistory:
        def __init__(self) -> None:
            pass
    
    def header(content : str, lvl : int):
        match lvl:
            case 1:
                write("="*15, f" {content} ", "="*15)
            
            case 2:
                write("-"*15, f") {content} (", "-"*15)
    

    # item related
    def use_combat_item_outside_combat():
        write("You shouldn't use an offensive item outside of combat")
    
    # player related
    def player_healed(hp_before : int, additional_hp : int, hp_delta : int, current_hp : int):
        write(f"The player was healed for {additional_hp} HP{f' (capped at {hp_delta} HP)' if additional_hp != hp_delta else ''}. HP: {hp_before} -> {current_hp}")
    
    def player_max_hp_increased(previous_max_hp : int, current_max_hp : int):
        write(f"The player's max HP has increased! Max HP: {previous_max_hp} -> {current_max_hp}")
    
    def player_bonus_dmg_increased(previous_dmg_bonus : int, current_dmg_bonus : int):
        write(f"The player's dmg bonus has increased! Dmg bonus: {previous_dmg_bonus} -> {current_dmg_bonus}")
    
    # entity related
    def entity_received_effect(entity_name : str, effect_type : str, dmg : int, duration : int):
        write(f"The {entity_name} has been hit by a {effect_type} effect, dealing {dmg} DMG for {duration} rounds")
    
    def entity_took_dmg(entity_name : str, dmg : int, hp_remaining : int, is_alive : int):
        entity_pronoun = "you" if entity_name == "player" else "it"
        write(
            f"The {entity_name} took {dmg} damage",
            (
                f". {hp_remaining} HP remaining" if is_alive else
                    f", killing {entity_pronoun} in the process"
            )
            )
    

    # room related
    def entered_room(room_type : str):
        text_options = INTERACTION_DATA.get(room_type, None)
        if text_options != None:
            write(choice(text_options))
    
    def stepped_in_trap(min_roll_to_escape : int):
        write(f"You stepped in a trap! Roll at least {min_roll_to_escape} to save yourself")
    
    def escaped_trap(roll : int, harmed : bool):
        write(f"You rolled {roll} and", ('managed to escape unharmed' if not harmed else 'was harmed by the trap while escaping'), sep=" ")
