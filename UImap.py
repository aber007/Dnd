def openUIMap(size, map):
    import tkinter as tk
    windowsize = 300

    main = tk.Tk()
    main.title("Map")
    main.wm_geometry(f"300x300+0+0")
    main.configure(bg="black")
    main.wm_attributes("-ontop")
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
    main.bind("<Escape>", lambda e: main.destroy())
    main.mainloop()


if __name__ == "__main__":
    openUIMap(5, map=None)