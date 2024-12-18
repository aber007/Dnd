from . import CONSTANTS, ITEM_DATA, ROOM_DATA, get_user_action_choice, wait_for_key, Log, Console, Lore


def eye_of_horus(player):
    map = player.parent_map
    current_room = map.get_room(player.position)

    action_options = [f"Cast on door facing {direction}" for direction in current_room.doors]
    action_idx = get_user_action_choice("Choose direction to cast the Eye of Horus: ", action_options)

    selected_direction = action_options[action_idx].rsplit(" ", 1)[-1]
    coord_offset = {"N": [0,-1], "E": [1,0], "S": [0,1], "W": [-1,0]}[selected_direction]
    
    selected_room_coords = player.position + coord_offset
    selected_room = map.get_room(selected_room_coords)

    selected_room.horus_was_used = True
    if selected_room.is_cleared:
        map.UI_instance.send_command("tile", selected_room_coords, ROOM_DATA["ui_colors"]["discovered"])
    else:
        map.UI_instance.send_command("tile", selected_room_coords, ROOM_DATA["ui_colors"][selected_room.type])
    Log.used_eye_of_horus(selected_direction, ROOM_DATA["contains_text"][selected_room.type])

class Item:
    def __init__(self, item_id : str) -> None:
        self.id = item_id
        self.parent_inventory : Inventory | None = None

        # get the attributes of the given item_id and make them properties of this object
        [setattr(self, k, v) for k,v in ITEM_DATA[item_id].items()]
    
    def use(self) -> any:
        """If the item is offensive, return its damage\n
        If the item isnt offensive return a callable requiring 1 argument, player. This callable is expected to called in main"""

        return_val : any = None

        match self.type:
            case "weapon":
                return_val = self.effect
    
            case "potion":
                if self.affects == "dice":
                    return_val = lambda player: player.active_dice_effects.append(self.effect)
            
            case "spell":
                match self.id:
                    case "the_eye_of_horus":
                        return_val = eye_of_horus
                    
                    case "breath_of_life":
                        return_val = lambda player: player.heal(self.effect)
                    
                    case "breath_of_fire":
                        return_val = self.effect
                    
        
        self.durability -= 1
        if self.durability == 0:
            Log.item_broke()
            self.parent_inventory.remove_item(self)
        
        return return_val

    def is_broken(self) -> bool:
        return 0 == self.durability
    
    def __str__(self):
        return self.name[0].upper() + self.name[1:]



class Inventory:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.size = CONSTANTS["player_inventory_size"]
        self.chosen_weapon = None
        self.slots : list[Item | None] = [None] * self.size # this length should never change
        
        self.receive_item(Item("sharp_twig"), supress_log=True)

        self.gold = CONSTANTS["player_starting_gold"]
        self.exp = CONSTANTS["player_starting_exp"]
        self.lvl = CONSTANTS["player_starting_lvl"]
    
    def is_full(self):
        """if all slots arent None, return True"""
        return all(self.slots)
    
    def get_items(self, include_emtpy = False):
        """Returns the content of all slots that arent None except if include_empty is True"""
        if include_emtpy:
            return self.slots
        else:
            return [item for item in self.slots if item != None]

    def receive_item(self, item : Item, supress_log : bool = False):
        if not supress_log:
            Log.received_item(item.name_in_sentence, item.description)

        item.parent_inventory = self

        if item.name == "Note":
            Lore.discovered_page()
            return

        if self.is_full():
            if not supress_log:
                Log.newline()
                Log.received_item_inventory_full()
            action_options = self.get_items() + [f"New item: {item}"]
            action_idx = get_user_action_choice("Choose item to throw out: ", action_options)
            selected_item = action_options[action_idx]

            # if the selected item is the last option, aka the new item
            if selected_item == action_options[-1]:
                if not supress_log: Log.item_thrown_out(item.name)
                return
            else:
                if not supress_log: Log.item_thrown_out(selected_item.name)
                self.remove_item(selected_item)
        
        # set the first found empty slot to the received item
        first_found_empty_slot_idx = self.slots.index(None)
        self.slots[first_found_empty_slot_idx] = item

    def remove_item(self, item : Item) -> None:
        item.parent_inventory = None

        # this removes the item from the list, making later items move 'upwards'
        self.slots.remove(item)
        self.slots.append(None)

    def update_lvl(self) -> bool:
        """Returns wether the player leveled up"""
        new_lvl = CONSTANTS["player_exp_to_lvl_func"](self.exp)
        lvl_delta = new_lvl - self.lvl
        self.lvl = new_lvl

        Log.player_lvl_up(self.lvl, lvl_delta)
        
        exp_til_next_lvl = CONSTANTS["player_lvl_to_exp_func"](self.lvl + 1) - self.exp
        Log.player_exp_til_next_lvl(exp_til_next_lvl)

        # since on_lvl_up prints stuff to console: receive skill points down here 
        if 0 < lvl_delta:
            Log.newline()
            self.parent.on_lvl_up()
            self.parent.receive_skill_point(lvl_delta)
        
        return bool(lvl_delta)

    def get_lvl(self) -> int:
        return int(self.lvl)


    def open(self, item_select_start_y : int = 0) -> Item | None:
        """If an item was used return that item to be processed by the function that called this function\n
        If no item was used return None"""

        return_item : Item | None = None
        items_in_inventory = self.get_items(include_emtpy=True)

        Console.save_cursor_position("inventory start")
        Log.view_inventory(self, items_in_inventory)
        Log.newline()

        action_options = ["Choose item", "View skill tree", "Cancel"]
        action_idx = get_user_action_choice("Choose action: ", action_options, start_y=item_select_start_y)

        match action_options[action_idx]:
            case "Choose item":
                return_item = self.select_item_to_use()
            
            case "View skill tree":
                Console.save_cursor_position("view skill tree start")
                Log.view_skill_tree(self.parent)
                Console.truncate("view skill tree start")

            case "Cancel":
                Console.truncate("inventory start")
                return None

        Console.truncate("inventory start")

        # recursively call this function until the player either
        #     cancelled the at the 'show inventory' dialog or an item was selected
        # this allows the player to: show inventory -> show use item dialog -> cancel use item -> show inventory.
        #     in other words, cancelling the use of an item doesnt close the inventory
        if return_item == None:
            return self.open(item_select_start_y=action_idx)
        else:
            return return_item

    def select_item_to_use(self) -> Item | None:
        """Returns an item or none, depending on if the user cancelled"""

        selected_item : Item | None = None
        items_in_inventory = self.get_items()

        Console.save_cursor_position("select item start")
        Log.header("USE ITEM", 1)

        if len(items_in_inventory):
            action_options = items_in_inventory + ["Cancel"]
            action_idx = get_user_action_choice("Choose item to use: ", action_options)

            match action_options[action_idx]:
                case "Cancel":
                    selected_item = None
                case _item:
                    selected_item = _item

        else:
            Log.inventory_empty()
            Log.newline()
            wait_for_key("[Press ENTER to continue]", "Return")
        
        Console.truncate("select item start")
        return selected_item


