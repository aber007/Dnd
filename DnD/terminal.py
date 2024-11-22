# This file is dedicated to interactive terminal utils that are more advanced than just input()
# These comments exist to clarify the difference between terminal.py, logger.py and console_io.py

from . import CONSTANTS, Console, ANSI, PlayerInputs

import os, time, shutil, typing, math
from random import randint

try:
    import keyboard
except ImportError:
    os.system("pip install keyboard")
    import keyboard


def write(*s : str, sep="", end="", flush=True) -> int:
    """Similar to print() except using custom default variables\n
    Also returns the amount of line count written to console"""
    return Console.write(*s, sep=sep, end=end)

class ItemSelect:
    def __init__(self, items : list[str], action_options_prefixes : list[str] | None = None, subtexts : list[str] | None = None, log_controls : bool = False, header : str = "", start_y : int = 0) -> None:
        """A fancy item selection function in the terminal.\n
        DO NOT use newlines in items or subtext as it will break the ItemSelect functionality.\n
        Tabs are allowed.\n
        Use the subtext param to write extra information about an item right below it in the terminal"""

        # create a list containing information about each action_option
        # if prefixes or subtexts were submitted: add them to the dict
        self.items = [{"text": str(item), "raw_value": item} for item in items]
        self.subtext_enabled = False
        
        if action_options_prefixes != None:
            [item_dict.update({"prefix": action_options_prefixes[idx]}) for idx,item_dict in enumerate(self.items)]
        if subtexts != None:
            [item_dict.update({"subtext": "\n" + subtexts[idx]}) for idx,item_dict in enumerate(self.items)]
            self.subtext_enabled = True
        
        
        self.start_y = start_y
        self.y_max = len(self.items)-1
        self.y = 0

        self.log_controls = log_controls
        self.header = header

        self.run_loop = True

    def start(self) -> str:
        PlayerInputs.register_input("Up", lambda : self.set_y_relative(-1))
        PlayerInputs.register_input("Down", lambda : self.set_y_relative(+1))
        PlayerInputs.register_input("Return", lambda : setattr(self, "run_loop", False))

        write("[Press ENTER to confirm and arrow UP/DOWN to navigate]\n" if self.log_controls else "")

        write(self.header, "\n")
        self.list_items()

        self.loop()

        write(ANSI.Cursor.move_down * (self.y_max - self.y + 1) * (2 if self.subtext_enabled else 1), ANSI.Cursor.set_x_0, "\n")
        return self.items[self.y]["raw_value"]

    def list_items(self):
        # write out all items and their subtexts
        write(*[item.get("prefix", "") + item["text"] + item.get("subtext", "") for item in self.items], sep="\n")

        # reposition the cursor to y = 0 and mark that item as selected
        write(ANSI.Cursor.set_x_0, ANSI.Cursor.move_up * (len(self.items) * (2 if self.subtext_enabled else 1) - 1))
        self.select_current_line()

        # reposition the cursor to the given start y
        self.set_y_relative(self.start_y - self.y)
    
    def set_y_relative(self, y_delta):
        # make sure we're not moving out of range
        if not (0 <= self.y + y_delta <= self.y_max):
            return

        self.deselect_current_line()

        if y_delta < 0:
            write(ANSI.Cursor.set_x_0, ANSI.Cursor.move_up * abs(y_delta) * (2 if self.subtext_enabled else 1))
        elif 0 < y_delta:
            write(ANSI.Cursor.set_x_0, ANSI.Cursor.move_down * abs(y_delta) * (2 if self.subtext_enabled else 1))
        
        self.y += y_delta
        self.select_current_line()
    
    def deselect_current_line(self):
        write(ANSI.Cursor.set_x_0, ANSI.Color.off, self.items[self.y].get("prefix", ""), ANSI.Color.off, self.items[self.y]["text"], ANSI.Color.off)

    def select_current_line(self):
        write(ANSI.Cursor.set_x_0, ANSI.Color.off, self.items[self.y].get("prefix", ""), ANSI.Color.off, ANSI.Color.selected_bg, ANSI.Color.selected_fg, self.items[self.y]["text"], ANSI.Color.off)

    def loop(self):
        while self.run_loop:
            PlayerInputs.check_inputs()
            time.sleep(1/20)
        
        PlayerInputs.unregister_all()

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
        PlayerInputs.register_input("Up", lambda : self.set_x(self.x_max))
        PlayerInputs.register_input("Down", lambda : self.set_x(0))
        PlayerInputs.register_input("Right", lambda : self.set_x(self.x+1))
        PlayerInputs.register_input("Left", lambda : self.set_x(self.x-1))
        PlayerInputs.register_input("Return", lambda : setattr(self, "run_loop", False))

        write("[Press ENTER to confirm and arrow UP/DOWN/LEFT/RIGHT to navigate]\n" if self.log_controls else "")

        self.write_header()
        self.set_x(0)

        self.loop()

        write(ANSI.Cursor.set_x_0, "\n")
        return self.x

    def write_header(self):
        # 8 is the len of " - ┤" and "├ +"
        slider_width = 8 + self.length

        pad_len = (slider_width - len(self.header))//2
        header_w_padding = f"{' '*pad_len}{self.header}"
        write(header_w_padding, "\n", flush=False)

    def set_x(self, new_x):
        new_x = min(self.x_max, max(0, new_x))

        # if the slider value changed
        if new_x != self.x and self.on_value_changed != None:
            self.on_value_changed(new_x)

        self.x = new_x
        
        write(ANSI.clear_line, " - ┤", ANSI.Color.selected_bg, " "*self.x, ANSI.Color.off, " "*(self.x_max-self.x), "├ +")

    def loop(self):
        while self.run_loop:
            PlayerInputs.check_inputs()
            time.sleep(1/20)
        
        PlayerInputs.unregister_all()


class Bar:
    def __init__(self, length : int, val : int | float, min_val : int | float, max_val : int | float, fill_color : ANSI.RGB, prefix : str = " ", min_val_min_width : int = 0) -> None:
        percent_done = (val-min_val)/(max_val-min_val)
        bars_to_fill = math.ceil(length * percent_done)
        min_val_str = str(min_val).rjust(min_val_min_width, " ")

        write(prefix + f"{min_val_str} ┤", fill_color, " "*bars_to_fill, ANSI.Color.off, " "*(length-bars_to_fill), f"├ {max_val}", "\n")


def ensure_terminal_width(desired_width):
    terminal_width = shutil.get_terminal_size((120, 55)).columns

    if desired_width <= terminal_width:
        return
    
    while (terminal_width :=  shutil.get_terminal_size((120, 55)).columns) < desired_width:
        # clears the previous line and replaces the text with the below
        write(ANSI.clear_line, f"Terminal {desired_width-terminal_width} characters too thin")
        time.sleep(1/20)
        
    # clears the previous line and replaces the text with the below
    write(ANSI.clear_line, f"Terminal size is good!")
    time.sleep(2)

    # clears the entire terminal and sets cursor pos top left
    write(ANSI.cls)

def wait_for_key(msg: str, key : str):
    write(msg)
    PlayerInputs.wait_for_key(key)


def combat_bar():
    red_length = 10
    orange_length = 6
    green_length = 2

    line_segments = [
        (ANSI.RGB(255, 0, 0, "bg"), red_length),
        (ANSI.RGB(255, 165, 0, "bg"), orange_length),    
        (ANSI.RGB(0, 255, 0, "bg"), green_length),      
        (ANSI.RGB(255, 0, 0, "bg"), 30-red_length-green_length-orange_length)
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
                    line_with_box += f"{color}{' ' * length}{ANSI.Color.off}"
                else:
                    # Partial or full overlap
                    left_empty = max(0, box_start - segment_start)
                    box_fill = max(0, min(box_end, segment_end) - max(box_start, segment_start))
                    right_empty = length - left_empty - box_fill

                    line_with_box += (
                        f"{color}{' ' * left_empty}{ANSI.Color.off}"  # Spaces before the box
                        f"{ANSI.RGB(255, 255, 255, 'bg')}{' ' * box_fill}{ANSI.Color.off}"  # The box
                        f"{color}{' ' * right_empty}{ANSI.Color.off}"  # Spaces after the box
                    )


                position += length

            write(ANSI.Cursor.set_x_0, line_with_box)
            if i==0:
                time.sleep(1)
            time.sleep(1/(2.5*(1+i)))

            # Check if ENTER was pressed
            if enter_pressed["status"]:
                break

    # Attach the ENTER key listener
    print("\nPress ENTER on the indication to Attack")
    keyboard.on_press_key("enter", on_enter, suppress=True)

    # Animate the box over the line
    animate_box()

    # Return the current box position if ENTER was pressed
    write("\n")
    if enter_pressed["status"]:
        keyboard.unhook_all()
        time.sleep(1)
        if box_position["start"] >= red_length and box_position["start"] < red_length+orange_length:
            return("hit")
        elif box_position["start"] >= red_length+orange_length and box_position["start"] < red_length+orange_length+green_length:
            return("hit_x2")
        else:
            return("miss")
    
    else:
        return "miss"



class DodgeEnemyAttack:
    def __init__(self) -> None:
        self.length = CONSTANTS["dodge_bar_length"]
        self.colors = {name : ANSI.RGB(*color_values, "bg") for name,color_values in CONSTANTS["dodge_bar_colors"].items()}
        self.times = CONSTANTS["dodge_bar_times"]
        self.dmg_factors = CONSTANTS["dodge_bar_dmg_factors"]

        self.enter_pressed = False
    
    def start(self):
        """Returns the enemy's damage factor"""
        
        # Decide the time before the bar turns green
        wait_time = self.times["waiting"] + randint(-self.times["waiting_range"], self.times["waiting_range"])

        write("Press ENTER when the bar is green or orange to dodge\n")
        time.sleep(1)
        PlayerInputs.register_input("Return", lambda : setattr(self, "enter_pressed", True))

        # make the bar red and wait for wait_time or enter_pressed
        write(self.colors["red"], " "*self.length, ANSI.Color.off)
        self.wait(wait_time)
        if self.enter_pressed:
            write("\nYou failed to dodge the attack\n")
            self.on_finished()
            return self.dmg_factors["red"]

        # make the bar green and wait until the perfect_dodge zone has passed or enter_pressed
        write(ANSI.clear_line, self.colors["green"], " "*self.length, ANSI.Color.off)
        self.wait(self.times["perfect_dodge"])
        if self.enter_pressed:
            write("\nYou perfectly dodged the attack\n")
            self.on_finished()
            return self.dmg_factors["green"]
        
        # make the bar orange and wait until the partial_dodge zone has passed or enter_pressed
        write(ANSI.clear_line, self.colors["orange"], " "*self.length, ANSI.Color.off)
        self.wait(self.times["partial_dodge"] - self.times["perfect_dodge"])
        if self.enter_pressed:
            write("\nYou partially dodged the attack\n")
            self.on_finished()
            return self.dmg_factors["orange"]
        
        # at this point the user has missed both opportunities to dodge
        #    therefore display the red bar and return red
        write(ANSI.clear_line, self.colors["red"], " "*self.length, ANSI.Color.off, "\nYou failed to dodge the attack\n")
        self.on_finished()
        return self.dmg_factors["red"]
    
    def wait(self, ms) -> None:
        """Wait for ms or enter_pressed"""
        start_time = time.time()
        seconds_to_wait = ms/1000

        while time.time() - start_time < seconds_to_wait and not self.enter_pressed:
            PlayerInputs.check_inputs()
            time.sleep(1/20)

    def on_finished(self):
        PlayerInputs.unregister_all()
        time.sleep(1)



if __name__ == "__main__":
    ensure_terminal_width(100)
    
    action_options = ["this is option 1", "this is option 2", "this is option 3"]
    subtexts = ["\tthis is subtext 1", "\tthis is subtext 2", "\tthis is subtext 3"]
    menu = ItemSelect(items=action_options, subtexts=subtexts)
    return_val = menu.start()
    print(return_val)

    # wait_for_key("\n[Press ENTER to continue]\n", "Return")

    # slider = Slider(20, header="Example header")
    # return_val = slider.start()
    # print(return_val)

    # Bar(30, 3, 0, 15, RGB(242,13,13,"bg"), "Player health: ")

    # combat_bar()
