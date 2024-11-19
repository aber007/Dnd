from . import CONSTANTS, ItemSelect

def get_user_action_choice(choose_message : str, action_options : list[str], subtexts : list[str] | None = None) -> str:
    """Have the user select an action for a list of actions\n
    Choose message is the string the player will see when prompted to choose. Recomended example: 'Choose action: '\n
    The index of the selected action in action_options is returned\n

    With fancy item selection:\n
        The user uses a dynamic menu in the console controlled by arrow UP, arrow DOWN and ENTER
    With normal item selection:\n
        The user enters a digit corresponding to the action they would like to choose\n
        Retry until a valid answer has been given"""


    if CONSTANTS["use_fancy_item_selection"]:
        print(choose_message)
        selected_item = ItemSelect(action_options, subtexts).start()
        return action_options.index(selected_item)
    else:
        print("\n".join(f"{idx+1}) {action}\n{subtexts[idx] if subtexts != None else ''}" for idx,action in enumerate(action_options)))
        
        while True:
            action_nr : str[int] = input(choose_message)
            err, err_mesage = check_user_input_error(action_nr, action_options)
            if err:
                print(err_mesage, end="\n"*2)
            else:
                break
        
        return int(action_nr)-1
    

def check_user_input_error(action_nr : str, action_options : list[str]) -> tuple[bool, str]:
    """Checks if the user's input is valid. If not: return (True, "error message"), otherwise: return (False, "")"""
    
    if not action_nr.isdigit():
        return (True, f"'{action_nr}' isn't a valid option")

    if not (0 < int(action_nr) <= len(action_options)):
        return (True, f"'{action_nr}' is out of range")
    
    return (False, "")