"""
Tom = 0, 0.2
Monster = 1, 0.4
Kista = 2, 0.2
Fälla = 3, 0.1
Shop = 4, 0.1
"""
def createmap(size):
    if size % 2 == 0:
        raise ValueError ("Size must not be even")
    typer = [0,1,2,3,4]
    sannolikhet = [0.2,0.4,0.2,0.1,0.1]
    from random import choices


    "2D map"
    map = [[0 for x in range(size)] for y in range(size)]

    "Assign random values to each location with set probabilites"
    for x in range(size):
        for y in range(size):
            if x == int(size/2+1)-1 and y == int(size/2+1)-1:
                map[x][y] = 0
            else:
                typ = choices(typer, sannolikhet)
                map[x][y] = typ[0]
                print(typ)
            
    return map
    
if __name__ == "__main__":
    size = 5
    map = createmap(size)
    for i in range(size):
        print(map[i])
