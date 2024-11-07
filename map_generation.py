"""
Empty = 10, 0.2
Monster = 20, 0.4
Chest = 30, 0.2
Trap = 40, 0.1
Shop = 50, 0.1
"""
def createmap(size):
    if size % 2 == 0:
        size += 1
    types = ["Empty","Monster","Chest","Trap","Shop"]
    probabilities = [0.2,0.4,0.2,0.1,0.1]
    from random import choices


    "Initialize 2D array"
    map = [[0 for x in range(size)] for y in range(size)]
    class Room:
        def __init__(self, type, discovered, open_doors) -> None:
            self.type = type
            self.discovered = discovered
            self.open_doors = open_doors

    "Assign random values to each location with set probabilites"
    for x in range(size):
        for y in range(size):
            if x == int(size/2+1)-1 and y == int(size/2+1)-1:
                map[x][y] = Room(type="Empty", discovered=True, open_doors=["N", "S", "E", "W"])
            else:
                roomtype = str(choices(types, probabilities))
                map[x][y] = Room(type=roomtype, discovered=False, open_doors=["N", "S", "E", "W"])


        
    return map
    
if __name__ == "__main__":
    size = 3
    map = createmap(size)    
