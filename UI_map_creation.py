import threading
from time import sleep
from map_generation import createmap
import random
def openUIMap(size, map):
    import tkinter as tk
    global main
    global grids
    
    windowsize = 300

    main = tk.Tk()
    main.title("Map")
    main.wm_geometry(f"300x300+0+0")
    main.configure(bg="black")
    main.wm_attributes("-topmost", "true")
    main.overrideredirect(True)

    xcord = int(size)
    ycord = int(size)
    "Create grids"
    
    grids = {}
    grid_width = windowsize / ycord
    grid_height = windowsize / xcord
    
    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            key = f"{row:02d}{col:02d}"
            grids[key] = tk.Frame(main, bg="gray", width=grid_width, height=grid_height)
            grids[key].place(x=(col - 1) * grid_width, y=(row - 1) * grid_height)

    "Create Walls"
    walls = {}
    wall_thickness = 5

    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            if random.randint(1,4) < 2 and row+col != len(map):
                frame_key = f"{row:02d}{col:02d}"
                if col < ycord:
                    walls[f"{frame_key}x"] = tk.Frame(grids[frame_key], bg="white", width=wall_thickness, height=grid_height)
                if row < xcord:
                    walls[f"{frame_key}y"] = tk.Frame(grids[frame_key], bg="white", width=grid_width, height=wall_thickness)

    for key, wall in walls.items():
        if 'x' in key:
            wall.place(relx=1.0, y=0, anchor='ne')
        elif 'y' in key:
            wall.place(x=0, rely=1.0, anchor='sw')
        def destroy():
            main.destroy()
            return None
    main.bind("<Escape>", lambda e: destroy())
    main.mainloop()

def update(map):
    global grids
    for x in range(len(map)):
        for y in range(len(map)):
            key = f"{x+1:02d}{y+1:02d}"
            print(map[x][y])
            if map[x][y].discovered == True:
                print("Even")
                grids[key].configure(bg="gray")
            else:
                print("Odd")
                print(map[x][y].type)
                if map[x][y].type == "Empty":
                    grids[key].configure(bg="gray")
                elif map[x][y].type == "Monster":
                    grids[key].configure(bg="red")
                elif map[x][y].type == "Chest":
                    grids[key].configure(bg="yellow")
                elif map[x][y].type == "Trap":
                    grids[key].configure(bg="black")
                elif map[x][y].type == "Shop":
                    grids[key].configure(bg="blue")



if __name__ == "__main__":
    size = 5
    map = createmap(size)
    threading.Thread(target=openUIMap, args=(size, map)).start()
    sleep(0.2)
    update(map)
    