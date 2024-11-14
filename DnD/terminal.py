import os, time, sys

try:
    import keyboard
except ImportError:
    os.system("pip install keyboard")
    import keyboard


cursor_move_up = f"\033[{1}A"
cursor_move_down = f"\033[{1}B"
cursor_move_right = f"\033[{1}C"
cursor_move_left = f"\033[{1}D"
cursor_show_cursor = "\033[?25h"
cursor_hide_cursor = "\033[?25l"
cursor_x_0 = "\r"
cursor_clear_line = cursor_x_0 + "\033[K"
cursor_clear_terminal = "\033[2J"
cursor_set_xy_top_left = "\033[H"


color_rgb_fg = lambda r,g,b: f"\u001b[38;2;{r};{g};{b}m"
color_rgb_bg = lambda r,g,b: f"\u001b[48;2;{r};{g};{b}m"
color_selected_bg = color_rgb_bg(255,255,255)
color_selected_fg = color_rgb_fg(0,0,0)
color_off = "\u001b[0m"



def write(*s : str, sep="") -> None:
    sys.stdout.write(sep.join(str(_s) for _s in s))
    sys.stdout.flush()

class ItemSelect:
    def __init__(self, items : list[str]) -> None:
        self.items = items
        self.y_max = len(self.items)-1
        self.y = 0

        self.run_loop = True

    def start(self) -> str:
        keyboard.on_press_key("up", lambda _ : self.set_y(self.y-1), suppress=True)
        keyboard.on_press_key("down", lambda _ : self.set_y(self.y+1), suppress=True)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "run_loop", False), suppress=True)

        write("[Press ENTER to confirm and arrow UP/DOWN to navigate]\n", cursor_hide_cursor)
        self.list_items()
        self.set_y(0)

        self.loop()

        write(cursor_show_cursor, cursor_move_down * (self.y_max - self.y + 1), cursor_x_0, "\n")
        return self.items[self.y]

    def list_items(self):
        write(*self.items, sep="\n")
        self.y = self.y_max
    
    def set_y(self, new_y):
        self.deselect_current_line()

        new_y = min(self.y_max, max(0, new_y))

        delta = new_y - self.y
        if delta < 0:
            write(cursor_move_up * abs(delta))
        else:
            write(cursor_move_down * abs(delta))
        
        self.y = new_y
        self.select_current_line()

    def deselect_current_line(self):
        write(cursor_x_0, color_off, self.items[self.y], color_off)

    def select_current_line(self):
        write(cursor_x_0, color_selected_bg, color_selected_fg, self.items[self.y], color_off)

    def loop(self):
        while self.run_loop:
            time.sleep(1/20)
        
        keyboard.unhook_all()

class Slider():
    def __init__(self, length : int) -> None:
        self.length = length
        self.x = 0
        self.x_max = length-1

        self.run_loop = True

    def start(self) -> str:
        keyboard.on_press_key("up",    lambda _ : self.set_x(self.x_max), suppress=True)
        keyboard.on_press_key("down",  lambda _ : self.set_x(0), suppress=True)
        keyboard.on_press_key("right", lambda _ : self.set_x(self.x+1), suppress=True)
        keyboard.on_press_key("left",  lambda _ : self.set_x(self.x-1), suppress=True)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "run_loop", False), suppress=True)

        write("[Press ENTER to confirm and arrow UP/DOWN/LEFT/RIGHT to navigate]\n", cursor_hide_cursor)
        self.set_x(0)

        self.loop()

        write(cursor_show_cursor, cursor_x_0, "\n")
        return self.x

    def set_x(self, new_x):
        new_x = min(self.x_max, max(0, new_x))
        self.x = new_x
        
        write(cursor_clear_line, " - ┤", color_selected_bg, " "*self.x, color_off, " "*(self.x_max-self.x), "├ +")

    def loop(self):
        while self.run_loop:
            time.sleep(1/20)
        
        keyboard.unhook_all()

def ensure_terminal_width(desired_width):
    terminal_width = os.get_terminal_size().columns

    if desired_width <= terminal_width:
        return
    
    while (terminal_width := os.get_terminal_size().columns) < desired_width:
        # clears the previous line and replaces the text with the below
        write(cursor_clear_line, f"Terminal {desired_width-terminal_width} characters too thin")
        time.sleep(1/20)
        
    # clears the previous line and replaces the text with the below
    write(cursor_clear_line, f"Terminal size is good!")
    time.sleep(2)

    # clears the entire terminal and sets cursor pos top left
    write(cursor_clear_terminal, cursor_set_xy_top_left)

def wait_for_key(msg: str, key : str):
    write(msg)
    keyboard.wait(key, suppress=True)


if __name__ == "__main__":
    # ensure_terminal_width(100)
    
    # menu = ItemSelect(items=["This is item 1", "This is item 2", "This is item 3"])
    # return_val = menu.start()
    # print(return_val)

    # wait_for_key("\n[Press ENTER to continue]\n", "enter")

    slider = Slider(20)
    return_val = slider.start()
    print(return_val)
