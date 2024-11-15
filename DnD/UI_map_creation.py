import tkinter as tk
import random
import time
from . import Array2D, Vector2, CONSTANTS

def openUIMap(size : int, rooms : Array2D[any], player_pos : Vector2, command_queue):
    # Setup parameters
    windowsize = 300
    size = Vector2(double=size)
    tile_width = windowsize / size.x
    tile_height = windowsize / size.y

    # Initial configurations
    global algorithm_status, live_update, possible_moves, current_location, backtrack_status, existing_walls
    current_location = [0, 0]
    algorithm_status = True
    live_update = True
    backtrack_status = False
    backtrack = []
    possible_moves = []
    locations_to_avoid = {}  # Define this as per the maze walls
    existing_walls = {}

    # Tkinter setup
    main = tk.Tk()
    main.title("DnD map")
    main.geometry(f"{windowsize}x{windowsize}+0+0")
    main.configure(bg="black")
    main.attributes("-topmost", True)
    main.overrideredirect(True)

    for x in range(size.x):
        for y in range(size.y):
            locations_to_avoid[f"{x}.{y}"] = False
    locations_to_avoid["0.0"] = True

    debug = True

            

    # Grid and player setup

    bg_Canvas = tk.Canvas(main, bg="gray", width=300, height=300)
    bg_Canvas.place(relheight=1, relwidth=1)

    grid = Array2D.create_frame_by_size(width=size.x, height=size.y)
    for x, y, _ in grid:
        grid[x,y] = tk.Frame(bg_Canvas, bg="gray", width=tile_width, height=tile_height, border=None)
        grid[x,y].place(x=x * tile_width, y=y * tile_height)

    walls : tk.Frame = {}
    wall_thickness = tile_height/20

    for x in range(size.x):
        for y in range(size.y):
            if y < size.y and x != size.x-1:  # Vertical wall on the right side of each cell
                walls[(x, y, 'E')] = tk.Frame(
                    grid[x,y], bg="black", width=wall_thickness, height=tile_height
                )
                walls[(x, y, 'E')].place(relx=1.0, y=0, anchor='ne')
                existing_walls[f"{x}.{y}.E"] = True
            
            if x < size.x and y != size.y-1:  # Horizontal wall on the bottom side of each cell
                walls[(x, y, 'S')] = tk.Frame(
                    grid[x,y], bg="black", width=tile_width, height=wall_thickness
                )
                walls[(x, y, 'S')].place(x=0, rely=1.0, anchor='sw')
                existing_walls[f"{x}.{y}.S"] = True

    # Player icon setup
    player_icon = tk.Frame(main, bg="magenta2", width=tile_width / 3, height=tile_height / 3)
    player_icon.place(x=current_location[1] * tile_width, y=current_location[0] * tile_height)

    # Define movement functions
    def move_north():
        global current_location
        last_location = current_location.copy()
        current_location[0] -= 1
        update_player_position(last_location)

    def move_south():
        global current_location
        last_location = current_location.copy()
        current_location[0] += 1
        update_player_position(last_location)

    def move_west():
        global current_location
        last_location = current_location.copy()
        current_location[1] -= 1
        update_player_position(last_location)

    def move_east():
        global current_location
        last_location = current_location.copy()
        current_location[1] += 1
        update_player_position(last_location)

    def update_player_position(last_location):
        player_icon.place(x=current_location[1] * tile_width, y=current_location[0] * tile_height)
        locations_to_avoid[str(current_location[0])+"."+str(current_location[1])] = True
        if backtrack_status == False:
            if last_location != current_location:
                if last_location[0] == current_location[0]:
                    if last_location[1] > current_location[1]:
                        if debug:
                            walls[(current_location[1], current_location[0], 'E')].place_forget()
                        existing_walls[f"{current_location[1]}.{current_location[0]}.E"] = False
                    else:
                        if debug:
                            walls[(current_location[1]-1, (current_location[0]), 'E')].place_forget()
                        existing_walls[f"{current_location[1]-1}.{current_location[0]}.E"] = False
                if last_location[1] == current_location[1]:
                    if last_location[0] > current_location[0]:
                        if debug:
                            walls[(current_location[1], current_location[0], 'S')].place_forget()
                        existing_walls[f"{current_location[1]}.{current_location[0]}.S"] = False
                    else:
                        if debug:
                            walls[((current_location[1]), current_location[0]-1, 'S')].place_forget()
                        existing_walls[f"{current_location[1]}.{current_location[0]-1}.S"] = False
    # Algorithm function
    def algorithm():
        global algorithm_status, live_update, backtrack_status, possible_moves, current_location

        while algorithm_status:
            possible_moves.clear()
            
            # Check each direction for possible moves
            if current_location[0] > 0:  # NORTH
                if not locations_to_avoid.get(f"{current_location[0] - 1}.{current_location[1]}"):
                    possible_moves.append("NORTH")
            
            if current_location[0] < size.y - 1:  # SOUTH
                if not locations_to_avoid.get(f"{current_location[0] + 1}.{current_location[1]}"):
                    possible_moves.append("SOUTH")
            
            if current_location[1] > 0:  # WEST
                if not locations_to_avoid.get(f"{current_location[0]}.{current_location[1] - 1}"):
                    possible_moves.append("WEST")
            
            if current_location[1] < size.x - 1:  # EAST
                if not locations_to_avoid.get(f"{current_location[0]}.{current_location[1] + 1}"):
                    possible_moves.append("EAST")
            
            if not backtrack_status:
                backtrack.append(f"{current_location[0]}.{current_location[1]}")

            if not possible_moves:
                if current_location == [0, 0]:  # Maze completed
                    for key in existing_walls.keys():
                        if random.randint(1,5) == 1:
                            existing_walls[key] = False
                            key = key.split(".")
                            if debug:
                                walls[(int(key[0]), int(key[1]), key[2])].place_forget()
                            main.update()
                    algorithm_status = False
                    main.update()
                    return existing_walls

                backtrack_status = True
                if backtrack:
                    last_position = backtrack.pop()
                    x_val, y_val = map(int, last_position.split('.'))
                    current_location = [x_val, y_val]
            else:
                rand_index = random.randint(0, len(possible_moves) - 1)
                direction_to_move = possible_moves[rand_index]
                backtrack_status = False

                if direction_to_move == "NORTH":
                    move_north()
                elif direction_to_move == "SOUTH":
                    move_south()
                elif direction_to_move == "WEST":
                    move_west()
                elif direction_to_move == "EAST":
                    move_east()

            if live_update:
                main.update_idletasks()
                main.update()

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
    active_walls = algorithm()
    main.after(100, handle_command_queue)
    main.after(100, lambda : update_player_pos(player_pos))
    main.mainloop()

