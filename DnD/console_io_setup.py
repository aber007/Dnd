from . import ANSI
from io import StringIO
import sys, time

class _Console:
    def __init__(self) -> None:
        self.io = StringIO()

    def write(self, *s : str, sep : str = "", end : str = "\n", flush : bool = False, clear_on_flush : bool = True) -> int:
        """Similar to print() except using custom default variables\n
        Also returns the amount of line count written to console"""

        text = sep.join(str(_s) for _s in s) + end

        # if the inputted text has a "clear terminal" ANSI code:
        #    get the text that comes afterwards, then clear the terminal, then write the extracted text
        # this is done because the ANSI.clear_terminal code doesnt work
        if ANSI.clear_terminal in text:
            clear_on_flush = True
            text = text.rsplit(ANSI.clear_terminal, 1)[-1]
            self.clear()
        
        self.io.write(text)

        if flush:
            self.flush(clear_on_flush)

        return len(text.split("\n"))


    def flush(self, clear_on_flush : bool) -> int:
        self.io.flush()
        self.io.seek(0)

        text = self.io.read()

        if clear_on_flush:
            sys.stdout.write("\033[2J") #! prolly have to clear since it prints everything anyways. try doing it with buffered cursor pos and recall
        sys.stdout.write(text)
        sys.stdout.flush()
    
    def clear(self) -> int:
        self.io.flush()
        self.io.truncate(0)
        self.io.seek(0)
        self.io.flush()

Console = _Console()