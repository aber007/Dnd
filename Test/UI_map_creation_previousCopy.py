import os
from . import CONSTANTS, Array2D, Vector2
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk


def openUIMap(size : int, rooms : Array2D[any], player_pos : Vector2, command_queue):
    windowsize = 300

    main = tk.Tk()
    main.title("DnD map")
    main.wm_geometry(f"{windowsize}x{windowsize}+0+0")
    main.configure(bg="black")
    main.wm_attributes("-topmost", "true")
    main.overrideredirect(True)
    
    size = Vector2(double=size)

    # Setup and place grid tiles
    grid = Array2D.create_frame_by_size(width=size.x, height=size.y)
    tile_width = windowsize / size.x
    tile_height = windowsize / size.y
    
    for x, y, _ in grid:
        grid[x,y] = tk.Frame(main, bg="gray", width=tile_width, height=tile_height)
        grid[x,y].place(x=x * tile_width, y=y * tile_height)

    # Setup and place walls
    walls = Array2D.create_frame_by_size(width=size.x, height=size.y, val={"x": None, "y": None})
    wall_thickness = tile_width/20

    for x, y, _ in walls:
        if x < size.x:
            walls[x,y]["x"] = tk.Frame(grid[x,y], bg="black", width=wall_thickness, height=tile_height)
            walls[x,y]["x"].place(relx=1.0, y=0, anchor='ne')

        if y < size.y:
            walls[x,y]["y"] = tk.Frame(grid[x,y], bg="black", width=tile_width, height=wall_thickness)
            walls[x,y]["y"].place(x=0, rely=1.0, anchor='sw')

    # Setup player icon
    player_icon = tk.Frame(main, bg="magenta2", width=tile_width/3, height=tile_height/3)

    # Initial grid color update
    for x, y, room in rooms:
        if not room.discovered and CONSTANTS["debug"]["gray_map_tiles"]:
            grid[x,y].configure(bg=CONSTANTS["room_ui_colors"]["default"])
        
        else:
            grid[x,y].configure(bg=CONSTANTS["room_ui_colors"][room.type])


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
                    # update the bg color of the tile at position
                    tile_coords_str, bg_color = command.split(" ", 1)
                    tile_position = eval(f"Vector2({tile_coords_str})")
                    
                    grid[tile_position].configure(bg=bg_color)

                case "pp":
                    # reposition the player position rectangle
                    player_position = eval(f"Vector2({command})")
                    update_player_pos(player_position)
        
        # if there are more than 1 command in the queue: handle them all right away
        # since we wont be having thousands of commands per second recursion limit shouldnt be a problem
        if 1 < qsize:
            handle_command_queue()
        
        main.after(100, handle_command_queue)

    def update_player_pos(player_pos : Vector2):
        player_pos_grid_tile : tk.Frame = grid[player_pos]
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
