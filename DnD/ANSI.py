class ANSI:

    class RGB:
        def __init__(self, r : int, g : int, b : int, ground : str) -> None:
            """ground is either 'fg' or 'bg'"""

            self.rgb = [r,g,b]
            self.ground = ground
            self.ansi = ANSI.Color.rgb_bg(*self.rgb) if ground == "bg" else ANSI.Color.rgb_fg(*self.rgb)
        
        def __add__(self, part : str) -> str:
            return self.ansi + part

        def __str__(self) -> str:
            return self.ansi

    class Cursor:
        move_up = f"\033[{1}A"
        move_down = f"\033[{1}B"
        move_right = f"\033[{1}C"
        move_left = f"\033[{1}D"
        show = "\033[?25h"
        hide = "\033[?25l"
        set_x_0 = "\r"
        set_xy_0 = "\033[H"
    
    class Color:
        rgb_fg = lambda r,g,b: f"\033[38;2;{r};{g};{b}m"
        rgb_bg = lambda r,g,b: f"\033[48;2;{r};{g};{b}m"
        selected_bg = rgb_bg(255,255,255)
        selected_fg = rgb_fg(0,0,0)
        off = "\033[0m"
    
    class Text:
        off = "\033[0m"
        single_underline = "\033[4m"
        double_underline = "\033[21m"
    
    # clear_terminal = "\033[2J"
    # clear_terminal_buffer = "\033[3J"
    clear_line = Cursor.set_x_0 + "\033[K"
    cls = "\033c" # sets all console settings to default