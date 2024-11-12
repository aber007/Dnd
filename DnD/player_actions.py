def get_user_action_choice(choose_message : str, action_options : list[str]) -> str:
    """Have the user select an action for a list of actions. Retry until a valid answer has been given.\n
    Choose message is the string the player will see when prompted to choose. Recomended example: "Choose action: "\n
    The index of the selected action in action_options is returned"""
    print("\n".join(f"{idx+1}) {action}" for idx,action in enumerate(action_options)))
    
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