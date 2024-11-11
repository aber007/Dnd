# import threading
# from time import sleep
import os
from . import Vector2
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk

try:
    from multiprocessing import Process, Manager
except ImportError:
    os.system("pip install multiprocessing")
    from multiprocessing import Process, Manager


def openUIMap(size : int, rooms : list[list[any]], command_queue):
    windowsize = 300

    main = tk.Tk()
    main.title("Map")
    main.wm_geometry(f"{windowsize}x{windowsize}+0+0")
    main.configure(bg="black")
    main.wm_attributes("-topmost", "true")
    main.overrideredirect(True)

    xcord = int(size)
    ycord = int(size)
    
    # Setup and place grid tiles
    grids = {}
    grid_width = windowsize / ycord
    grid_height = windowsize / xcord
    
    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            key = f"{row:02d}{col:02d}"
            grids[key] = tk.Frame(main, bg="gray", width=grid_width, height=grid_height)
            grids[key].place(x=(col - 1) * grid_width, y=(row - 1) * grid_height)

    # Setup walls
    walls = {}
    wall_thickness = grid_width/20

    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            frame_key = f"{row:02d}{col:02d}"
            if col < ycord:
                walls[f"{frame_key}x"] = tk.Frame(grids[frame_key], bg="black", width=wall_thickness, height=grid_height)
            if row < xcord:
                walls[f"{frame_key}y"] = tk.Frame(grids[frame_key], bg="black", width=grid_width, height=wall_thickness)

    # Place walls
    for key, wall in walls.items():
        if 'x' in key:
            wall.place(relx=1.0, y=0, anchor='ne')
        elif 'y' in key:
            wall.place(x=0, rely=1.0, anchor='sw')

    # Initial grid color update
    for x in range(len(rooms)):
        for y in range(len(rooms)):
            key = f"{(y+1):02d}{(x+1):02d}" #Yes, this looks wrong but it's correct
            if rooms[x][y].discovered == True and rooms[x][y].type not in ["trap", "shop"]:
                grids[key].configure(bg="gray")
            else:
                if rooms[x][y].type == "empty":
                    grids[key].configure(bg="light gray")
                elif rooms[x][y].type == "enemy":
                    grids[key].configure(bg="red")
                elif rooms[x][y].type == "chest":
                    grids[key].configure(bg="yellow")
                elif rooms[x][y].type == "trap":
                    grids[key].configure(bg="dark green")
                elif rooms[x][y].type == "mimic_trap":
                    grids[key].configure(bg="light green")
                elif rooms[x][y].type == "shop":
                    grids[key].configure(bg="blue")

    def handle_command_queue():
        # not optimal but the other methods didnt work as expected 
        try:
            qsize = command_queue.qsize()
        except:
            destroy()
            return

        if qsize:
            # eg. command: "10,5 red"
            command = command_queue.get()

            tile_coords_str, bg_color = command.split(" ")
            x,y = list(map(lambda i : int(i), tile_coords_str.split(",")))
            
            key = f"{(y+1):02d}{(x+1):02d}"
            grids[key].configure(bg=bg_color)

        main.after(100, handle_command_queue)


    def destroy(_ = None):
        main.quit()
        main.destroy()
    
    main.bind("<Escape>", destroy)
    main.after(100, handle_command_queue)
    main.mainloop()
