from . import CONSTANTS, SKILL_TREE_DATA

import os, time, sys, shutil, typing, math
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
    def __init__(self, items : list[str], action_options_prefixes : list[str] | None = None, subtexts : list[str] | None = None, log_controls : bool = False, header : str = "") -> None:
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
        
        
        self.y_max = len(self.items)-1
        self.y = 0

        self.log_controls = log_controls
        self.header = header

        self.run_loop = True

    def start(self) -> str:
        keyboard.on_press_key("up", lambda _ : self.set_y_relative(-1), suppress=True)
        keyboard.on_press_key("down", lambda _ : self.set_y_relative(+1), suppress=True)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "run_loop", False), suppress=True)

        write("[Press ENTER to confirm and arrow UP/DOWN to navigate]\n" if self.log_controls else "", cursor_hide_cursor)

        write(self.header, "\n")
        self.list_items()

        self.loop()

        write(cursor_show_cursor, cursor_move_down * (self.y_max - self.y + 1) * (2 if self.subtext_enabled else 1), cursor_x_0, "\n")
        return self.items[self.y]["raw_value"]

    def list_items(self):
        # write out all items and their subtexts
        
        write(*[item.get("prefix", "") + item["text"] + item.get("subtext", "") for item in self.items], sep="\n")

        # reposition the cursor to y = 0 and mark that item as selected
        write(cursor_x_0, cursor_move_up * (len(self.items) * (2 if self.subtext_enabled else 1) - 1))
        self.select_current_line()
    
    def set_y_relative(self, y_delta):
        # make sure we're not moving out of range
        if not (0 <= self.y + y_delta <= self.y_max):
            return

        self.deselect_current_line()

        if y_delta < 0:
            write(cursor_x_0, cursor_move_up * abs(y_delta) * (2 if self.subtext_enabled else 1))
        elif 0 < y_delta:
            write(cursor_x_0, cursor_move_down * abs(y_delta) * (2 if self.subtext_enabled else 1))
        
        self.y += y_delta
        self.select_current_line()

    def deselect_current_line(self):
        write(cursor_x_0, color_off, self.items[self.y].get("prefix", ""), color_off, self.items[self.y]["text"], color_off)

    def select_current_line(self):
        write(cursor_x_0, color_off, self.items[self.y].get("prefix", ""), color_off, color_selected_bg, color_selected_fg, self.items[self.y]["text"], color_off)

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
    def __init__(self, length : int, val : int | float, min_val : int | float, max_val : int | float, fill_color : RGB, prefix : str = " ", min_val_min_width : int = 0) -> None:
        percent_done = (val-min_val)/(max_val-min_val)
        bars_to_fill = math.ceil(length * percent_done) 
        min_val_str = str(min_val).rjust(min_val_min_width, " ")

        write(prefix + f"{min_val_str} ┤", fill_color, " "*bars_to_fill, color_off, " "*(length-bars_to_fill), f"├ {max_val}", "\n")


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
    write(cursor_hide_cursor, msg)
    keyboard.wait(key, suppress=True)
    write(cursor_show_cursor)


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


        # Decide the time before the bar turns green
        wait_time = self.times["waiting"] + randint(-self.times["waiting_range"], self.times["waiting_range"])

        write(cursor_hide_cursor, "Press ENTER when the bar is green or orange to dodge\n")
        time.sleep(1)
        keyboard.on_press_key("enter", lambda _ : setattr(self, "enter_pressed", True), suppress=True)

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


def view_skill_tree(player):
    check_color = RGB(*CONSTANTS["skill_tree_check_color"], "fg")
    check_str = f"{check_color}✔{color_off}"
    cross_color = RGB(*CONSTANTS["skill_tree_cross_color"], "fg")
    cross_str = f"{cross_color}✖{color_off}"

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
    
    write(f"\n{'='*15} SKILL TREE {'='*15}\n\n")
    write("\n\n".join(formatted_branch_strings), "\n"*2)

    wait_for_key("\n[Press ENTER to continue]", "enter")
    

if __name__ == "__main__":
    ensure_terminal_width(100)
    
    action_options = ["this is option 1", "this is option 2", "this is option 3"]
    subtexts = ["\tthis is subtext 1", "\tthis is subtext 2", "\tthis is subtext 3"]
    menu = ItemSelect(items=action_options, subtexts=subtexts)
    return_val = menu.start()
    print(return_val)

    # wait_for_key("\n[Press ENTER to continue]\n", "enter")

    # slider = Slider(20, header="Example header")
    # return_val = slider.start()
    # print(return_val)

    # Bar(30, 3, 0, 15, RGB(242,13,13,"bg"), "Player health: ")

    # combat_bar()
