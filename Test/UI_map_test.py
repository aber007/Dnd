import tkinter as tk
import random
import time

# Setup parameters
windowsize = 300
size_x = 10  # Adjust grid dimensions as needed
size_y = 10
tile_width = windowsize / size_x
tile_height = windowsize / size_y

# Initial configurations
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

for x in range(size_x):
    for y in range(size_y):
        locations_to_avoid[f"{x}.{y}"] = False
locations_to_avoid["0.0"] = True


        

# Grid and player setup
grid = [[tk.Frame(main, bg="white", width=tile_width, height=tile_height) for _ in range(size_x+1)] for _ in range(size_y+1)]
for x in range(size_x):
    for y in range(size_y):
        grid[x][y].place(x=x * tile_width, y=y * tile_height)

walls : tk.Frame = {}
wall_thickness = tile_height/20

for x in range(size_x):
    for y in range(size_y):
        if y < size_y:  # Vertical wall on the right side of each cell
            walls[(x, y, 'E')] = tk.Frame(
                grid[x][y], bg="black", width=wall_thickness, height=tile_height
            )
            walls[(x, y, 'E')].place(relx=1.0, y=0, anchor='ne')
            existing_walls[f"{x}.{y}.E"] = True
        
        if x < size_x:  # Horizontal wall on the bottom side of each cell
            walls[(x, y, 'S')] = tk.Frame(
                grid[x][y], bg="black", width=tile_width, height=wall_thickness
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
                            walls[(current_location[1], current_location[0], 'E')].place_forget()
                            existing_walls[f"{current_location[1]}.{current_location[0]}.E"] = False
                        else:
                            walls[(current_location[1]-1, (current_location[0]), 'E')].place_forget()
                            existing_walls[f"{current_location[1]-1}.{current_location[0]}.E"] = False
                    if last_location[1] == current_location[1]:
                        if last_location[0] > current_location[0]:
                            walls[(current_location[1], current_location[0], 'S')].place_forget()
                            existing_walls[f"{current_location[1]}.{current_location[0]}.S"] = False
                        else:
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
        
        if current_location[0] < size_y - 1:  # SOUTH
            if not locations_to_avoid.get(f"{current_location[0] + 1}.{current_location[1]}"):
                possible_moves.append("SOUTH")
        
        if current_location[1] > 0:  # WEST
            if not locations_to_avoid.get(f"{current_location[0]}.{current_location[1] - 1}"):
                possible_moves.append("WEST")
        
        if current_location[1] < size_x - 1:  # EAST
            if not locations_to_avoid.get(f"{current_location[0]}.{current_location[1] + 1}"):
                possible_moves.append("EAST")
        
        if not backtrack_status:
            backtrack.append(f"{current_location[0]}.{current_location[1]}")

        if not possible_moves:
            if current_location == [0, 0]:  # Maze completed
                print("Maze Finished")
                algorithm_status = False
                main.update()
                return

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
            time.sleep(0.1)

# Start algorithm in main loop
main.after(100, algorithm)
main.bind("<Escape>", lambda e : main.destroy())
main.mainloop()
