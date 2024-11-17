from . import CONSTANTS

import typing
import os, time, sys, shutil
from random import randint

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


class RGB:
    def __init__(self, r : int, g : int, b : int, ground : str) -> None:
        """ground is either 'fg' or 'bg'"""

        self.r, self.g, self.b = r, g, b
        self.ground = ground

        self.ansi = color_rgb_bg(self.r, self.g, self.b) if ground == "bg" else color_rgb_fg(self.r, self.g, self.b)
    
    def __str__(self):
        return self.ansi


def write(*s : str, sep="") -> None:
    sys.stdout.write(sep.join(str(_s) for _s in s))
    sys.stdout.flush()

class ItemSelect:
    def __init__(self, items : list[str], log_controls : bool = False, header : str = "") -> None:
        self.items = items
        self.y_max = len(self.items)-1
        self.y = 0

        self.log_controls = log_controls
        self.header = header

        self.run_loop = True

    def start(self) -> str:
        keyboard.on_press_key("up", lambda _ : self.set_y(self.y-1), suppress=True)
        keyboard.on_press_key("down", lambda _ : self.set_y(self.y+1), suppress=True)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "run_loop", False), suppress=True)

        write("[Press ENTER to confirm and arrow UP/DOWN to navigate]\n" if self.log_controls else "", cursor_hide_cursor)

        write(self.header, "\n")
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

class Slider:
    def __init__(self, length : int, on_value_changed : typing.Callable[[int], None] | None = None, log_controls : bool = False, header : str = "") -> None:
        self.length = length
        self.x = 0
        self.x_max = length-1

        self.on_value_changed = on_value_changed
        self.log_controls = log_controls
        self.header = header

        self.run_loop = True

    def start(self) -> str:
        keyboard.on_press_key("up",    lambda _ : self.set_x(self.x_max), suppress=True)
        keyboard.on_press_key("down",  lambda _ : self.set_x(0), suppress=True)
        keyboard.on_press_key("right", lambda _ : self.set_x(self.x+1), suppress=True)
        keyboard.on_press_key("left",  lambda _ : self.set_x(self.x-1), suppress=True)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "run_loop", False), suppress=True)

        write("[Press ENTER to confirm and arrow UP/DOWN/LEFT/RIGHT to navigate]\n" if self.log_controls else "", cursor_hide_cursor)

        self.write_header()
        self.set_x(0)

        self.loop()

        write(cursor_show_cursor, cursor_x_0, "\n")
        return self.x

    def write_header(self):
        # 8 is the len of " - ┤" and "├ +"
        slider_width = 8 + self.length

        pad_len = (slider_width - len(self.header))//2
        header_w_padding = f"{' '*pad_len}{self.header}"
        write(header_w_padding, "\n")

    def set_x(self, new_x):
        new_x = min(self.x_max, max(0, new_x))

        # if the slider value changed
        if new_x != self.x and self.on_value_changed != None:
            self.on_value_changed(new_x)

        self.x = new_x
        
        write(cursor_clear_line, " - ┤", color_selected_bg, " "*self.x, color_off, " "*(self.x_max-self.x), "├ +")

    def loop(self):
        while self.run_loop:
            time.sleep(1/20)
        
        keyboard.unhook_all()


class Bar:
    def __init__(self, length : int, val : int | float, min_val : int | float, max_val : int | float, fill_color : RGB, prefix : str = " ") -> None:
        percent_done = (val-min_val)/(max_val-min_val)
        bars_to_fill = int(length * percent_done) + 1 #round up = round down + 1

        write(prefix + f"{min_val} ┤", fill_color, " "*bars_to_fill, color_off, " "*(length-bars_to_fill), f"├ {max_val}", "\n")


def ensure_terminal_width(desired_width):
    terminal_width = shutil.get_terminal_size((120, 55)).columns

    if desired_width <= terminal_width:
        return
    
    while (terminal_width :=  shutil.get_terminal_size((120, 55)).columns) < desired_width:
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


def combat_bar():
    red_length = 10
    orange_length = 6
    green_length = 2

    line_segments = [
        (RGB(255, 0, 0, "bg"), red_length),
        (RGB(255, 165, 0, "bg"), orange_length),    
        (RGB(0, 255, 0, "bg"), green_length),      
        (RGB(255, 0, 0, "bg"), 30-red_length-green_length-orange_length)
    ]
    line_length = sum(segment[1] for segment in line_segments)
    box_length = 1


    # Shared variable to track box position
    box_position = {"start": 0}
    enter_pressed = {"status": False}  # Shared variable for ENTER detection

    def on_enter(event):
        """Callback to capture ENTER key press."""
        enter_pressed["status"] = True

    # Function to animate the moving box
    def animate_box():
        for i in range(line_length - box_length + 1):
            # Update box position
            box_position["start"] = i

            # Generate the box overlay
            box_start = i
            box_end = i + box_length
            line_with_box = ""
            position = 0

            for color, length in line_segments:
                segment_start = position
                segment_end = position + length

                # Determine overlap with the box
                if box_end <= segment_start or box_start >= segment_end:
                    # No overlap
                    line_with_box += f"{color}{' ' * length}{color_off}"
                else:
                    # Partial or full overlap
                    left_empty = max(0, box_start - segment_start)
                    box_fill = max(0, min(box_end, segment_end) - max(box_start, segment_start))
                    right_empty = length - left_empty - box_fill

                    line_with_box += (
                        f"{color}{' ' * left_empty}{color_off}"  # Spaces before the box
                        f"{RGB(255, 255, 255, 'bg')}{' ' * box_fill}{color_off}"  # The box
                        f"{color}{' ' * right_empty}{color_off}"  # Spaces after the box
                    )


                position += length

            write(cursor_x_0, line_with_box)
            if i==0:
                time.sleep(1)
            time.sleep(1/(2.5*(1+i)))

            # Check if ENTER was pressed
            if enter_pressed["status"]:
                break

    # Attach the ENTER key listener
    print("\nPress ENTER on the indication to Attack")
    keyboard.on_press_key("enter", on_enter, suppress=True)

    write(cursor_hide_cursor)

    # Animate the box over the line
    animate_box()

    # Return the current box position if ENTER was pressed

    if enter_pressed["status"]:
        keyboard.unhook_all()
        time.sleep(1)
        write(cursor_show_cursor, "\n")
        if box_position["start"] >= red_length and box_position["start"] < red_length+orange_length:
            return("hit")
        elif box_position["start"] >= red_length+orange_length and box_position["start"] < red_length+orange_length+green_length:
            return("hit_x2")
        else:
            return("miss")
    
    else:
        write(cursor_show_cursor, "\n")
        return "miss"



class DodgeEnemyAttack:
    def __init__(self) -> None:
        self.length = CONSTANTS["dodge_bar_length"]
        self.colors = {name : RGB(*color_values, "bg") for name,color_values in CONSTANTS["dodge_bar_colors"].items()}
        self.times = CONSTANTS["dodge_bar_times"]
        self.dmg_factors = CONSTANTS["dodge_bar_dmg_factors"]

        self.enter_pressed = False
    
    def start(self):
        """Returns the enemy's damage factor"""

        keyboard.on_press_key("enter", lambda _ : setattr(self, "enter_pressed", True), suppress=True)

        # Decide the time before the bar turns green
        wait_time = self.times["waiting"] + randint(-self.times["waiting_range"], self.times["waiting_range"])

        write(cursor_hide_cursor, "Press ENTER when the bar is green or orange to dodge\n")

        # make the bar red and wait for wait_time or enter_pressed
        write(self.colors["red"], " "*self.length, color_off)
        self.wait(wait_time)
        if self.enter_pressed:
            write("\nYou failed to dodge the attack\n")
            self.on_finished()
            return self.dmg_factors["red"]

        # make the bar green and wait until the perfect_dodge zone has passed or enter_pressed
        write(cursor_clear_line, self.colors["green"], " "*self.length, color_off)
        self.wait(self.times["perfect_dodge"])
        if self.enter_pressed:
            write("\nYou perfectly dodged the attack\n")
            self.on_finished()
            return self.dmg_factors["green"]
        
        # make the bar orange and wait until the partial_dodge zone has passed or enter_pressed
        write(cursor_clear_line, self.colors["orange"], " "*self.length, color_off)
        self.wait(self.times["partial_dodge"] - self.times["perfect_dodge"])
        if self.enter_pressed:
            write("\nYou partially dodged the attack\n")
            self.on_finished()
            return self.dmg_factors["orange"]
        
        # at this point the user has missed both opportunities to dodge
        #    therefore display the red bar and return red
        write(cursor_clear_line, self.colors["red"], " "*self.length, color_off, "\nYou failed to dodge the attack\n")
        self.on_finished()
        return self.dmg_factors["red"]
    
    def wait(self, ms) -> None:
        """Wait for ms or enter_pressed"""
        start_time = time.time()
        seconds_to_wait = ms/1000

        while time.time() - start_time < seconds_to_wait and not self.enter_pressed:
            time.sleep(1/20)

    def on_finished(self):
        keyboard.unhook_all()
        time.sleep(1)
        write(cursor_show_cursor)

    
    

if __name__ == "__main__":
    ensure_terminal_width(100)
    #combat_bar()
    # menu = ItemSelect(items=["This is item 1", "This is item 2", "This is item 3"])
    # return_val = menu.start()
    # print(return_val)

    # wait_for_key("\n[Press ENTER to continue]\n", "enter")

    # slider = Slider(20, header="Example header")
    # return_val = slider.start()
    # print(return_val)

    # Bar(30, 3, 0, 15, RGB(242,13,13,"bg"), "Player health: ")

    combat_bar()
