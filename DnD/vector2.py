class Vector2:
    def __init__(self, x : float | None = None, y : float | None = None, double : float | None = None) -> None:
        """When instancing this object pass either x and y OR double\n
        Double sets both x and y to its value"""

        self.x = x if (x != None and y != None) else double if (double != None) else 0
        self.y = y if (x != None and y != None) else double if (double != None) else 0
	
    def __getitem__(self, i):
        # enables cases like: x, y = Vector2(...)
        return [self.x, self.y][i]

    def __add__(self, part):
        """Only supports variable 'part' of type Vector2 or iterable"""
        if isinstance(part, Vector2):
            return Vector2(self.x + part.x, self.y + part.y)
        else:
            return Vector2(self.x + part[0], self.y + part[1])

    def __str__(self):
        return f"<Vector2({self.x}, {self.y})>"