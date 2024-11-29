from . import Console, Log, Lore, Music, get_user_action_choice, wait_for_key

class MainMenu:
    
    def __init__(self, game_started : bool) -> None:
        self.game_started = game_started
        
    def start(self):
        Console.clear()
        Log.header("MAIN MENU", 1)
        Console.save_cursor_position("main menu start")

        while True:
            if self.game_started:
                action_options = ["Continue Game", "Options", "Lore", "Help", "Quit Game"]
            else:
                action_options = ["Start Game", "Options", "Lore", "Help", "Quit Game"]
            action_idx = get_user_action_choice("", action_options)
            
            # remove the ItemSelect remains
            Console.truncate("main menu start")

            match action_options[action_idx]:
                case "Start Game" | "Continue Game":
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

        action_options = ["Change Music Volume", "Return"]
        action_idx = get_user_action_choice("", action_options)
        
        match action_options[action_idx]:
            case "Change Music Volume":
                Console.truncate("option menu start")
                Music.change_volume()
    
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