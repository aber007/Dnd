# import threading
# from time import sleep
import os
from . import CONSTANTS, Vector2
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk


def openUIMap(size : int, rooms : list[list[any]], player_pos : Vector2, command_queue):
    windowsize = 300

    main = tk.Tk()
    main.title("DnD map")
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
            key = f"{row:02d}{col:02d}" # this is y,x. NOT x,y
            grids[key] = tk.Frame(main, bg="gray", width=grid_width, height=grid_height)
            grids[key].place(x=(col - 1) * grid_width, y=(row - 1) * grid_height)

    # Setup walls
    walls = {}
    wall_thickness = grid_width/20

    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            frame_key = f"{row:02d}{col:02d}" # this is y,x. NOT x,y
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

    # Setup player icon
    player_icon = tk.Frame(main, bg="magenta2", width=grid_width/3, height=grid_height/3)

    # Initial grid color update
    for x in range(len(rooms)):
        for y in range(len(rooms)):
            key = f"{(y+1):02d}{(x+1):02d}" #Yes, this looks wrong but it's correct
            if rooms[x][y].discovered != True:
                grids[key].configure(bg=CONSTANTS["room_ui_colors"]["default"])
            else:
                grids[key].configure(bg=CONSTANTS["room_ui_colors"][rooms[x][y].type])

    def handle_command_queue():
        # not optimal but the other methods didnt work as expected 
        try:
            # throws errors (plural) if command_queue is offline
            qsize = command_queue.qsize()
        except:
            destroy()
            return

        if qsize:
            # eg. command = "tile 10,5 red" or "pp 4,2"
            raw_command = command_queue.get()

            command_type, command = raw_command.split(" ", 1)
            
            match command_type:
                case "tile":
                    # update the bg color of the tile
                    tile_coords_str, bg_color = command.split(" ", 1)
                    x,y = list(map(lambda i : int(i), tile_coords_str.split(",")))
                    
                    key = f"{(y+1):02d}{(x+1):02d}"
                    grids[key].configure(bg=bg_color)

                case "pp":
                    # reposition the player position rectangle
                    x,y = list(map(lambda i : int(i), command.split(",")))
                    update_player_pos(Vector2(x,y))
        
        # if there are more than 1 command in the queue: handle them all right away
        # since we wont be having thousands of commands per second recursion limit shouldnt be a problem
        if 1 < qsize:
            handle_command_queue()
        
        main.after(100, handle_command_queue)

    def update_player_pos(player_pos : Vector2):
        player_pos_grid_tile : tk.Frame = grids[f"{(player_pos.y+1):02d}{(player_pos.x+1):02d}"]
        player_icon.place(
            x=player_pos_grid_tile.winfo_x() + player_pos_grid_tile.winfo_reqwidth()/2 - player_icon.winfo_reqwidth()/2,
            y=player_pos_grid_tile.winfo_y() + player_pos_grid_tile.winfo_reqheight()/2 - player_icon.winfo_reqheight()/2
            )

    def destroy(_ = None):
        main.quit()
        main.destroy()
    
    main.bind("<Escape>", destroy)
    main.after(100, handle_command_queue)
    main.after(100, lambda : update_player_pos(player_pos))
    main.mainloop()
