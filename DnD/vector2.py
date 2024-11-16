from typing import Iterable

class Vector2:
    def __init__(self, x : int | float | None = None, y : int | float | None = None, double : int | float | None = None) -> None:
        """When instancing this object pass either x and y OR double\n
        Double sets both x and y to its value"""

        self.x = x if (x != None and y != None) else double if (double != None) else 0
        self.y = y if (x != None and y != None) else double if (double != None) else 0
    
    def copy(self):
        return Vector2(self.x, self.y)
	
    def __getitem__(self, i : int) -> int | float:
        # enables cases like: 'x, y = Vector2(...)' and 'x = Vector2(...)[0]'
        return [self.x, self.y][i]

    def __add__(self, part : Iterable[int | float]):
        # enables cases like: 'Vector2(...) + [x, y]'
        return Vector2(self.x + part[0], self.y + part[1])
    
    def __sub__(self, part : Iterable[int | float]):
        # enables cases like: 'Vector2(...) - [x, y]'
        return Vector2(self.x-part[0], self.y-part[1])
    
    def __rsub__(self, part : Iterable[int | float]):
        # enables cases like: '[x, y] - Vector2(...)'
        return Vector2(part[0]-self.x, part[1]-self.y)
    
    def __eq__(self, part : Iterable[int | float]):
        # enables cases like: 'Vector2(...) == [x, y]'
        return self.x == part[0] and self.y == part[1]
    
    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __str__(self):
        return f"<Vector2({self.x}, {self.y})>"
