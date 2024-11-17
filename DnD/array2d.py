from .vector2 import Vector2
from typing import TypeVar, Generic, Iterable, Tuple, Callable

# Generic[TypeVar("T")] enables typehints like 'def foo(rooms : Array2D[Map.Room]): ...'
class Array2D( Generic[TypeVar("T")] ):

    def __init__(self, *rows) -> None:
        """A custom 2D array class that supports item assignment and subscription with format x,y, rather than the traditional y,x\n
        To assign item use 'array_2d_instance[x,y] = new_val'\n
        To get/subscribe item use 'array_2d_instance[x,y]'"""
        self.rows = rows
        self.size = Vector2(len(self.rows[0]), len(self.rows))

    def has(self, coords : Iterable[int]) -> bool:
        """Checks wether coordinates exists in this Array2D"""
        return not self._check_idx_error(*coords, throw_error=False)
    
    def copy(self):
        return Array2D(*self.rows)
    
    def list(self):
        """Returns a list of all positions and values in the Array2D. Each item in the list consists of a tuple (x, y, val)"""
        return [ (x,y,self[x,y]) for y in range(len(self.rows)) for x in range(len(self.rows[0])) ]

    def _check_idx_error(self, x : int, y : int, throw_error : bool = True) -> bool | None:
        """Either throws an error or returns True if the coords are out of range, depending on 'throw_error'\n
        Otherwise retuns False"""

        x_max = len(self.rows[0])-1
        if not (0 <= x <= x_max):
            if throw_error: raise IndexError(f"x ({x}) not within range 0 -> {x_max} (incl.)")
            else: return True

        y_max = len(self.rows)-1
        if not (0 <= y <= y_max):
            if throw_error: raise IndexError(f"y ({y}) not within range 0 -> {y_max} (incl.)")
            else: return True
        
        return False

    def __setitem__(self, coords : Iterable[int], val : any) -> None:
        # enables cases like 'array2d[x,y] = val' and 'array2d[vector2] = val'
        x,y = coords
        self._check_idx_error(x,y)
        self.rows[y][x] = val

    def __getitem__(self, coords : Iterable[int]) -> any:
        # enables cases like 'array2d[x,y]' and 'array2d[vector2]'
        x,y = coords
        self._check_idx_error(x,y)
        return self.rows[y][x]
    
    def __iter__(self) -> Tuple[int, int, any]:
        # enables cases like 'for x, y, val in array2d: ...'
        return iter([(x,y,self[x,y]) for y in range(len(self.rows)) for x in range(len(self.rows[0]))])

    def __str__(self) -> str:
        return "[" + "\n ".join(str(row) for row in self.rows) + "]"
    

    # Util functions
    def create_frame_by_size(width : int, height : int, val : any = None, val_callable : Callable[[], any] | None = None):
        """Creates an Array2D object from 'width' and 'height'\n
        Every item in the array is set to 'val' or, if 'val_callable' is given, the return value of 'val_callable()'. 'val_callble' is prioritized\n
        This function is not meant to be used with an already established Array2D instance, but rather to create the frame of a new one"""

        rows = []
        for y in range(height):
            row = [val_callable() if val_callable != None else val for x in range(width)]
            rows.append(row)
        
        return Array2D(*rows)

    def get_xy_iter(width : int, height : int) -> Iterable[int]:
        """Use this instead of 'for x in range(...): for y in range(...): ...'\n
        Enables cases like 'for x, y in Array2D.get_xy_iter(): ...'"""
        return iter([(x,y) for y in range(height) for x in range(width)])