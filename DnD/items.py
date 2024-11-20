from . import CONSTANTS, ITEM_DATA, get_user_action_choice, view_skill_tree, Bar, RGB, Log


def eye_of_horus(player):
    map = player.parent_map
    current_room = map.get_room(player.position)

    action_options = [f"Cast on door facing {direction}" for direction in current_room.doors]
    action_idx = get_user_action_choice("Choose direction to cast the Eye of Horus: ", action_options)

    selected_direction = action_options[action_idx].rsplit(" ", 1)[-1]
    coord_offset = {"N": [0,-1], "E": [1,0], "S": [0,1], "W": [-1,0]}[selected_direction]
    
    selected_room_coords = player.position + coord_offset
    selected_room = map.get_room(selected_room_coords)

    map.UI_instance.send_command("tile", selected_room_coords, CONSTANTS["room_ui_colors"][selected_room.type])
    Log.used_eye_of_horus(selected_direction, CONSTANTS['room_contains_text'][selected_room.type])

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
                        return_val = lambda player: player.heal(self.effect + (player.hp//10))
                    
                    case "breath_of_fire":
                        return_val = self.effect
                    
        
        self.durability -= 1
        if self.durability == 0:
            Log.item_broke(self.name)
            self.parent_inventory.remove_item(self)
        
        return return_val

    
    def __str__(self):
        return self.name



class Inventory:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.size = CONSTANTS["player_inventory_size"]
        self.chosen_weapon = None
        self.slots : list[Item | None] = [None] * self.size # this length should never change
        self.slots[0] = Item("sharp_twig")

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

    def receive_item(self, item : Item):
        Log.received_item(item.name_in_sentence, item.description)

        item.parent_inventory = self

        if self.is_full():
            Log.received_item_inventory_full()
            action_options = self.get_items() + [f"New item: {item}"]
            action_idx = get_user_action_choice("Choose item to throw out: ", action_options)
            selected_item = action_options[action_idx]

            # if the selected item is the last option, aka the new item
            if selected_item == action_options[-1]:
                Log.item_thrown_out(item.name)
                return
            else:
                Log.item_thrown_out(selected_item.name)
                self.remove_item(selected_item)
        
        # set the first found empty slot to the received item
        first_found_empty_slot_idx = self.slots.index(None)
        self.slots[first_found_empty_slot_idx] = item

    def remove_item(self, item : Item) -> None:
        item.parent_inventory = None

        # this removes the item from the list, making later items move 'upwards'
        self.slots.remove(item)
        self.slots.append(None)

    def update_lvl(self):
        new_lvl = CONSTANTS["player_exp_to_lvl_func"](self.exp)
        lvl_delta = new_lvl - self.lvl
        self.lvl = new_lvl

        Log.player_lvl_up(self.lvl, lvl_delta)
        
        exp_til_next_lvl = CONSTANTS["player_lvl_to_exp_func"](self.lvl + 1) - self.exp
        Log.player_exp_til_next_lvl(exp_til_next_lvl)

        # since on_lvl_up prints stuff to console: receive skill points down here 
        if 0 < lvl_delta:
            self.parent.on_lvl_up()
            self.parent.receive_skill_point(lvl_delta)

    def get_lvl(self) -> int:
        return int(self.lvl)


    def open(self) -> Item | None:
        """If an item was used return that item to be processed by the function that called this function\n
        If no item was used return None"""

        return_item : Item | None = None
        items_in_inventory = self.get_items(include_emtpy=True)

        Log.header("INVENTORY", 1)
        self.list_player_stats()

        Log.list_inventory_items(items_in_inventory)

        action_options = ["Use item", "View skill tree", "Cancel"]
        action_idx = get_user_action_choice("Choose action: ", action_options)

        match action_options[action_idx]:
            case "Use item":
                return_item = self.select_item_to_use()
            
            case "View skill tree":
                view_skill_tree(self.parent)

            case "Cancel":
                return None
        
        # recursively call this function until the player either
        #     cancelled the at the 'show inventory' dialog or an item was selected
        # this allows the player to: show inventory -> show use item dialog -> cancel use item -> show inventory.
        #     in other words, cancelling the use of an item doesnt close the inventory
        if return_item == None:
            return self.open()
        else:
            return return_item

    def list_player_stats(self):
        print(f"Gold: {self.gold}")

        exp_bar_prefix = f"Player Lvl: {self.lvl}, EXP: {self.exp}   "
        hp_bar_prefix = f"Player HP: {self.parent.hp}   "
        longer_prefix = sorted([exp_bar_prefix, hp_bar_prefix], key=lambda i : len(i), reverse=True)[0]

        exp_bar_prefix = exp_bar_prefix.ljust(len(longer_prefix), " ")
        hp_bar_prefix = hp_bar_prefix.ljust(len(longer_prefix), " ")

        min_val_min_width = max(len(str(self.parent.hp)), len(str(self.exp)))

        # hp bar
        Bar(
            length=CONSTANTS["hp_bar_max_length"],
            val=self.parent.hp,
            min_val=0,
            min_val_min_width=min_val_min_width,
            max_val=self.parent.max_hp,
            fill_color=RGB(*CONSTANTS["hp_bar_fill_color"], "bg"),
            prefix=hp_bar_prefix
        )

        # exp bar
        Bar(
            length=CONSTANTS["exp_bar_max_length"],
            val=self.exp,
            min_val=CONSTANTS["player_lvl_to_exp_func"](self.lvl), # min exp for current lvl
            min_val_min_width=min_val_min_width,
            max_val=CONSTANTS["player_lvl_to_exp_func"](self.lvl+1), # min exp for next lvl
            fill_color=RGB(*CONSTANTS["exp_bar_fill_color"], "bg"),
            prefix=exp_bar_prefix
        )

        print(f"Permanent DMG bonus: {self.parent.permanent_dmg_bonus}", end="\n"*2)

    def select_item_to_use(self) -> Item | None:
        items_in_inventory = self.get_items()

        print(f"\n{'='*15} USE ITEM {'='*15}", end="\n"*2)

        if len(items_in_inventory):
            action_options = items_in_inventory + ["Cancel"]
            action_idx = get_user_action_choice("Choose item to use: ", action_options)

            match action_options[action_idx]:
                case "Cancel":
                    return None
                case _item:
                    return _item

        else:
            print("You have no items to use!")
            return None
    
    def __str__(self):
        lines = [f"\n{'='*15} INVENTORY {'='*15}"]

        for idx, item in enumerate(self.slots):
            lines.append(f"Slot {idx+1}: " + (item.name if item != None else ""))
        
        return "\n".join(lines)

