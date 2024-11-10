import threading
from time import sleep
from .map_generation import createmap
import os
try:
    import tkinter as tk
except ImportError:
    os.system("pip install tkinter")
    import tkinter as tk

close_thread = False

def openUIMap(size, map):
    global close_thread, main, grids 
    
    windowsize = 300

    main = tk.Tk()
    main.title("Map")
    main.wm_geometry(f"{windowsize}x{windowsize}+0+0")
    main.configure(bg="black")
    main.wm_attributes("-topmost", "true")
    main.overrideredirect(True)

    xcord = int(size)
    ycord = int(size)
    
    grids = {}
    grid_width = windowsize / ycord
    grid_height = windowsize / xcord
    
    for row in range(1, xcord + 1):
        for col in range(1, ycord + 1):
            key = f"{row:02d}{col:02d}"
            grids[key] = tk.Frame(main, bg="gray", width=grid_width, height=grid_height)
            grids[key].place(x=(col - 1) * grid_width, y=(row - 1) * grid_height)

    walls = {}
    wall_thickness = 5

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
        main.quit()
        main.destroy()
    
    def check_close():
        if close_thread:
            print("Trying to close")
            main.quit()
            main.destroy()
            print("Closed")
        else:
            main.after(100, check_close)  # Check every 100ms for close_thread update
    
    main.bind("<Escape>", lambda e: destroy)
    main.after(100, check_close)  # Start the periodic close check
    main.mainloop()


def create_UI_Map(size, map, close=False) -> None:
    global close_thread

    close_thread = False  # Reset close_thread at the start
    ui_thread = threading.Thread(target=openUIMap, args=(size, map))
    ui_thread.start()

    # Initial update and check for closure
    sleep(0.5)
    update(map)
    
    if close:
        close_thread = True  # Signal to close the UI
        ui_thread.join()     # Wait for the thread to exit


#Updating the map after movement. Needs to be ran after each move
def update(map):
    global grids

    if close_thread:
        return  # Skip update if close flag is set
    
    for x in range(len(map)):
        for y in range(len(map)):
            key = f"{(y+1):02d}{(x+1):02d}" #Yes, this looks wrong but it's correct
            if map[x][y].discovered == True and map[x][y].type != "trap":
                grids[key].configure(bg="gray")
            else:
                if map[x][y].type == "empty":
                    grids[key].configure(bg="light gray")
                elif map[x][y].type == "enemy":
                    grids[key].configure(bg="red")
                elif map[x][y].type == "chest":
                    grids[key].configure(bg="yellow")
                elif map[x][y].type == "trap":
                    grids[key].configure(bg="dark green")
                elif map[x][y].type == "mimic_trap":
                    grids[key].configure(bg="light green")
                elif map[x][y].type == "shop":
                    grids[key].configure(bg="blue")




if __name__ == "__main__":
    size = 5
    map = createmap(size)
    create_UI_Map(size, map)
    