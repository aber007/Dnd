# This file is dedicated to a custom IO object that enables convenient reversal of things written to console. ie .save_cursor_position and .truncate
# This system also prevents an issue where cursor movement in the console is limited to whats being visually displayed
# These comments exist to clarify the difference between terminal.py, logger.py and console_io.py

from . import ANSI
from io import StringIO
import sys

class _Console:
    def __init__(self) -> None:
        self.io = StringIO()
        self.saved_positions = {}

    def write(self, *s : str, sep : str = "", end : str = "\n") -> int:
        """Similar to print() except using custom default variables\n
        Also returns the amount of line count written to console"""

        text = sep.join(str(_s) for _s in s) + end
        
        self.io.write(text)
        self.write_to_console(text)

        return len(text.split("\n"))

    def write_to_console(self, text : str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def dump_to_console(self, clear_before_dump : bool = True) -> None:
        """Writes the entirety of the text stored in self.io to console.\n
        clear_before_dump decides wether the output console should be cleared before dumping the text"""
        
        if clear_before_dump:
            self.clear(custom_console=False)
        
        self.write_to_console(self.io.getvalue())

    def clear(self, custom_console : bool = True, output_console : bool = True, final : bool = False) -> int:
        """Clear the contents of the custom console (this object) and the output console (the one player sees) depending on the given args"""
        if custom_console:
            self.io.truncate(0)
            self.io.seek(0)
        
        if output_console:
            self.write_to_console(ANSI.cls + ANSI.Cursor.hide)
        
        if final:
            self.write_to_console(ANSI.Cursor.show)

    def save_cursor_position(self, key : str) -> None:
        """Stores the current position of the cursor for later use\n
        The position is saved in .saved_positions[key]"""
        self.saved_positions[key] = self.io.tell()
    
    def truncate(self, key : str, del_key_afterwards : bool = False) -> None:
        """Clear the console from the key til the end of the console.\n
        The key is the one used when saving the cursor position in save_cursor_position\n
        If the key doesnt exist nothing happens\n
        del_key_afterwards decides wether the key used should be deleted from .saved_positions"""

        if key not in self.saved_positions:
            return
        
        position = self.saved_positions[key]
        self.io.truncate(position)
        self.io.seek(position)

        self.dump_to_console(clear_before_dump=True)
        
        if del_key_afterwards:
            self.saved_positions.pop(key)

Console = _Console()