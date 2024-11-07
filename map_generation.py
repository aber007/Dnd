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
    types = [10,20,30,40,50]
    probabilities = [0.2,0.4,0.2,0.1,0.1]
    from random import choices


    "Initialize 2D array"
    map = [[0 for x in range(size)] for y in range(size)]

    "Assign random values to each location with set probabilites"
    for x in range(size):
        for y in range(size):
            if x == int(size/2+1)-1 and y == int(size/2+1)-1:
                map[x][y] = 11
            else:
                typ = choices(types, probabilities)
                map[x][y] = typ[0]
                print(typ)
            
    return map
    
if __name__ == "__main__":
    size = 5
    map = createmap(size)
    print(map)
    for i in range(size):
        print(map[i])
