from .vector2 import Vector2
from typing import TypeVar, Generic, Iterable, Tuple

# Generic[TypeVar("T")] enables typehints like 'def foo(rooms : Array2D[Map.Room]): ...'
class Array2D( Generic[TypeVar("T")] ):

    def __init__(self, *rows) -> None:
        """A custom 2D array class that supports item assignment and subscription with format x,y, rather than the traditional y,x\n
        To assign item use 'array_2d_instance[x,y] = new_val'\n
        To get/subscribe item use 'array_2d_instance[x,y]'"""
        self.rows = rows
        self.size = Vector2(len(self.rows[0]), len(self.rows))
    
    def create_frame_by_size(width : int, height : int, val : any = None):
        """Creates an Array2D object from 'width' and 'height'. Every item in the array is set to 'val'\n
        This function is not meant to be used with an already established Array2D instance, but rather to create the frame of a new one"""

        rows = []
        for y in range(height):
            rows.append([val for x in range(width)])
        
        return Array2D(*rows)

    def _check_idx_error(self, x : int, y : int) -> None:
        x_max = len(self.rows[0])-1
        if not (0 <= x <= x_max):
            raise IndexError(f"x ({x}) not within range 0 -> {x_max} (incl.)")

        y_max = len(self.rows)-1
        if not (0 <= y <= y_max):
            raise IndexError(f"y ({y}) not within range 0 -> {y_max} (incl.)")

    def __setitem__(self, coords : Iterable[int], val : any) -> None:
        # enables cases like 'array2d[x,y] = val'
        x,y = coords
        self._check_idx_error(x,y)
        self.rows[y][x] = val

    def __getitem__(self, coords : Iterable[int]) -> any:
        # enables cases like 'array2d[x,y]'
        x,y = coords
        self._check_idx_error(x,y)
        return self.rows[y][x]
    
    def __iter__(self) -> Tuple[int, int, any]:
        # enables cases like 'for x, y, val in array2d: ...'
        return iter([(x,y,self[x,y]) for y in range(len(self.rows)) for x in range(len(self.rows[0]))])

    def __str__(self) -> str:
        return "[" + "\n ".join(str(row) for row in self.rows) + "]"
