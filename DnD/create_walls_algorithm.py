from random import choice, choices
from . import (
    CONSTANTS,
    Vector2,
    Array2D,
    )

class CreateWallsAlgorithm:
    def __init__(self, size : int, starting_location : Vector2) -> None:
        self.size = size

        self.starting_location = starting_location
        self.current_location = self.starting_location.copy()

        self.currently_backtracking = False
        self.previous_locations : list[Vector2] = []

        self.map_frame : Array2D[bool] = Array2D.create_frame_by_size(self.size, self.size, val=False)

        self.locations_to_avoid : Array2D[bool] = self.map_frame.copy()
        self.locations_to_avoid[0,0] = True # Define this as per the maze walls

        # visualization of why only the East and South walls are definied:
        #    https://postimg.cc/tZXy3j5H
        #    as you can see all squares (except the edges) have 4 walls using this pattern
        #    when reading and attempting to understand the wall algorithm code its recommended to use the linked image as reference
        self.existing_walls : Array2D[dict[str,bool]] = Array2D.create_frame_by_size(self.size, self.size, val_callable=lambda : {"E": True, "S": True})


    def start(self) -> Array2D[dict[str,bool]]:
        while True:
            possible_moves = self.get_possible_moves()
            
            if not self.currently_backtracking:
                self.previous_locations.append(self.current_location)


            # if there are any possible moves
            if 0 < len(possible_moves):
                self.backtrack_status = False
                direction_to_move = choice(possible_moves)
                self.move(direction_to_move)

            else:
                # if the player hasnt been able to move
                if self.current_location == self.starting_location:
                    # remove remove_door_percent% of doors
                    wall_deletion_options = self.existing_walls.list()
                    for x, y, _ in choices(wall_deletion_options, k=round(len(wall_deletion_options) * CONSTANTS["remove_door_percent"])):
                        self.existing_walls[x,y][choice(["E","S"])] = False
                    
                    break

                self.currently_backtracking = True
                if 0 < len(self.previous_locations):
                    previous_location = self.previous_locations.pop()
                    self.current_location = previous_location
                else:
                    # if we are here then the algorithm is trying to backtrack
                    #    but there are no previous moves to use, which happens ~5% of the time
                    #    this can happen if the algorithm walk path completely surrounds the starting_position
                    #    solve this by simply redoing the algorithm and exiting the broken one once the new algorithms has finished
                    return CreateWallsAlgorithm(self.size, self.starting_location).start()

        return self.existing_walls

    def get_possible_moves(self) -> list[str]:
        """Check each direction for possible moves"""
        possible_moves = []
        for direction,coord_offset in CONSTANTS["directional_coord_offsets"].items():
            new_location = self.current_location + coord_offset
            if self.map_frame.has(new_location) and self.locations_to_avoid[new_location] == False:
                possible_moves.append(direction)
        
        return possible_moves

    def move(self, direction : str):
        self.last_location = self.current_location.copy()
        self.current_location += CONSTANTS["directional_coord_offsets"][direction]
        self.update_walls()

    def update_walls(self):
        """Disable the walls the algorithm has moved through"""

        # dont return to this location
        self.locations_to_avoid[self.current_location] = True

        # if we're currently backtracking OR the position hasnt changed: return
        if self.backtrack_status != False or self.last_location == self.current_location:
            return

        position_delta = self.current_location - self.last_location

        # if y didnt change, aka x changed
        if position_delta.y == 0:
            # we've moved east
            if position_delta == CONSTANTS["directional_coord_offsets"]["E"]:
                # in the last room disable the wall facing the current room
                self.existing_walls[self.last_location]["E"] = False
            
            # we've moved west
            else:
                # in the current room disable the wall facing the previous room
                self.existing_walls[self.current_location]["E"] = False

        # if x didnt change, aka y changed
        if position_delta.x == 0:
            # we've moved south
            if position_delta == CONSTANTS["directional_coord_offsets"]["S"]:
                # in the last room disable the wall facing the current room
                self.existing_walls[self.last_location]["S"] = False
            
            # we've moved north
            else:
                # in the current room disable the wall facing the previous room
                self.existing_walls[self.current_location]["S"] = False
