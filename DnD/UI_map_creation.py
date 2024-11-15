import os
from . import CONSTANTS, Array2D, Vector2, Animation, AnimationLibrary
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk

def grid_coords_to_real_coords(grid : Array2D[tk.Frame], coords : Vector2):
    """Takes coords and gets the tile at that position in grids. Returns the 'real' coords relative to the tk window"""
    grid_tile : tk.Frame = grid[*coords]
    return Vector2(
        grid_tile.winfo_x() + grid_tile.winfo_reqwidth()/2,
        grid_tile.winfo_y() + grid_tile.winfo_reqheight()/2
    )
    


def openUIMap(size : int, rooms : Array2D[any], player_pos : Vector2, command_queue):
    # used for smooth player repositioning
    anim_library = AnimationLibrary()

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
    player_icon.grid_position = player_pos

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
                    new_player_position = eval(f"Vector2({command})")
                    position_delta = new_player_position - player_icon.grid_position

                    # NOTE: the below code doesnt not work for diagonal movement
                    # run an animation where the player position rectangle's x OR y value is progressively changed from start_val to end_val a set duration
                    # the updating of these animations is handled by function 'update_anims' thats located near the end of this file
                    if position_delta.x != 0:
                        anim = Animation(
                            start_val=        player_icon.winfo_x(),
                            end_val=          grid_coords_to_real_coords(grid, new_player_position).x - player_icon.winfo_reqwidth()/2,
                            duration=         CONSTANTS["player_movement_anim_duration"],
                            on_val_update=    lambda v : player_icon.place(x=v, y=player_icon.winfo_y()),
                            on_anim_finished= lambda v : setattr(player_icon.grid_position, "x", new_player_position.x)
                            )
                        
                        anim_library.add_anim(anim)

                    if position_delta.y != 0:
                        anim = Animation(
                            start_val=        player_icon.winfo_y(),
                            end_val=          grid_coords_to_real_coords(grid, new_player_position).y - player_icon.winfo_reqheight()/2,
                            duration=         CONSTANTS["player_movement_anim_duration"],
                            on_val_update=    lambda v : player_icon.place(x=player_icon.winfo_x(), y=v),
                            on_anim_finished= lambda v : setattr(player_icon.grid_position, "y", new_player_position.y)
                            )
                        
                        anim_library.add_anim(anim)
        
        # if there were more than 1 command in the queue before the recently processed command was deleted: handle them all right away
        # since we wont be having thousands of commands per second recursion limit shouldnt be a problem
        if 1 < qsize:
            handle_command_queue()
        
        main.after(100, handle_command_queue)

    def update_player_pos_tile(coords : Vector2) -> None:

        player_pos_grid_tile : tk.Frame = grid[*coords]
        player_icon.place(
            x=player_pos_grid_tile.winfo_x() + player_pos_grid_tile.winfo_reqwidth()/2 - player_icon.winfo_reqwidth()/2,
            y=player_pos_grid_tile.winfo_y() + player_pos_grid_tile.winfo_reqheight()/2 - player_icon.winfo_reqheight()/2
            )
            
        player_icon.grid_position = coords
        

    def update_anims():
        anim_library.update_anims()

        # the animation update delay decreases when animations are running
        #    this means if there are no active anims this loop uses less computer resources
        #    if on the other hand there are animations running then use more resources to make them smoother
        #    the hz update rate of the animations is calculated with 1000/CONSTANTS["player_movement_anim_active_update_delay"]
        anim_update_delay_ms = CONSTANTS["player_movement_anim_active_update_delay"] if anim_library.has_active_animations else 50
        main.after(anim_update_delay_ms, update_anims)

    def destroy(_ = None):
        main.quit()
        main.destroy()
    
    main.bind("<Escape>", destroy)
    main.after(100, handle_command_queue)
    main.after(100, lambda : update_player_pos_tile(player_pos))
    main.after(100, update_anims)
    main.mainloop()
