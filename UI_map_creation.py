import threading
from time import sleep
from map_generation import createmap
import os
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk
def openUIMap(size, map):
    
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
    existing_walls = []

    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
                frame_key = f"{row:02d}{col:02d}"
                if col < ycord:
                    walls[f"{frame_key}x"] = tk.Frame(grids[frame_key], bg="black", width=wall_thickness, height=grid_height)
                if row < xcord:
                    walls[f"{frame_key}y"] = tk.Frame(grids[frame_key], bg="black", width=grid_width, height=wall_thickness)

                

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
            key = f"{(x+1):02d}{(y+1):02d}"
            if map[x][y].discovered != True:
                grids[key].configure(bg="gray")
            else:
                if map[x][y].type == "empty":
                    grids[key].configure(bg="gray")
                elif map[x][y].type == "enemy":
                    grids[key].configure(bg="red")
                elif map[x][y].type == "chest":
                    grids[key].configure(bg="yellow")
                elif map[x][y].type == "trap":
                    grids[key].configure(bg="brown")
                elif map[x][y].type == "shop":
                    grids[key].configure(bg="blue")



def create_UI_Map(size, map) -> None:
    threading.Thread(target=openUIMap, args=(size, map)).start()
    sleep(0.5)
    update(map)

if __name__ == "__main__":
    size = 5
    map = createmap(size)
    create_UI_Map(size, map)
    