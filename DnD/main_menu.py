from . import Console, Log, Lore, Music, get_user_action_choice, wait_for_key

class MainMenu:
    
    def __init__(self, game_started : bool) -> None:
        self.game_started = game_started
        self.difficulty = "escape"
        self.difficulty_str = "Escape the castle"

        # write a key hint the first time the player sees the main menu
        # dont show the hint if the menu was opened mid game since the player would already know the controls
        self.first_time_opening = False if game_started else True
        
        
    def start(self):
        Console.clear()
        Log.header("MAIN MENU", 1)
        Console.save_cursor_position("main menu start")

        if self.first_time_opening:
            Log.main_menu_key_hint()
            self.first_time_opening = False

        while True:
            if self.game_started:
                action_options = ["Continue Game", "Options", "Lore", "Help", "Quit Game"]
            else:
                action_options = ["Start Game", "Options", "Lore", "Help", "Quit Game"]
            action_idx = get_user_action_choice("", action_options)
            
            # remove the ItemSelect remains
            Console.truncate("main menu start")

            match action_options[action_idx]:
                case "Start Game":
                    return self.difficulty
                
                case "Continue Game":
                    return

                case "Options":
                    self.submenu_options()
                
                case "Lore":
                    self.submenu_lore()
                
                case "Help":
                    self.submenu_help()
                
                case "Quit Game":
                    exit_game()
            
            # remove the remains of eg. the options header
            Console.truncate("main menu start")

    def submenu_options(self):
        Log.header("OPTIONS", 2)
        Console.save_cursor_position("option menu start")

        if self.game_started:
            action_options = ["Change Music Volume", "Return"]
        else:
            action_options = ["Change Music Volume", "Change Difficulty", "Return"]

        action_idx = get_user_action_choice("", action_options)
        
        match action_options[action_idx]:
            case "Change Music Volume":
                Console.truncate("option menu start")
                Music.change_volume()
            
            case "Change Difficulty":
                Log.header("Choose Difficulty", 2)
                Log.show_current_difficulty(self.difficulty_str)

                difficulty_options = ["Escape the castle", "Reach lvl 10"]
                action_idx = get_user_action_choice("", difficulty_options)
                
                Log.write(f"Difficulty set to: {difficulty_options[action_idx]}")
                Log.newline()
                wait_for_key("Press ENTER to go back", "Return")
                
                self.difficulty_str = difficulty_options[action_idx]
                match difficulty_options[action_idx]:
                    case "Escape the castle":
                        self.difficulty = "escape"
                    case "Reach lvl 10":
                        self.difficulty = "lvl"

    def submenu_lore(self):
        Log.header("Lore", 2)
        Log.write_lore_pages(Lore.get_pages())
        Log.newline()
        Log.end()

        wait_for_key("Press ENTER to go back", "Return")

    def submenu_help(self):
        Log.header("Help", 2)
        Log.write_controls()
        Log.newline()
        Log.end()

        wait_for_key("Press ENTER to go back", "Return")


def exit_game():
    Log.write("Exiting game...")
    raise SystemExit