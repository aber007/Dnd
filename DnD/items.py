from . import CONSTANTS, ITEM_DATA, get_user_action_choice


def eye_of_horus(player):
    map = player.parent_map
    current_room = map.get_room(player.position)

    action_options = [f"Cast on door facing {direction}" for direction in current_room.doors]
    action_idx = get_user_action_choice("Choose direction to cast the Eye of Horus: ", action_options)

    selected_direction = action_options[action_idx].rsplit(" ", 1)[-1]
    coord_offset = {"N": [0,-1], "E": [1,0], "S": [0,1], "W": [-1,0]}[selected_direction]
    
    selected_room_coords = player.position + coord_offset

    map.UI_instance.send_command("tile", selected_room_coords, CONSTANTS["room_ui_colors"][map.get_room(player.position).type])

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
            print(f"\n{self.name} broke and is now useless!", end="\n"*2)
            self.parent_inventory.remove_item(self)
        
        return return_val

    
    def __str__(self):
        return self.name



class Inventory:
    def __init__(self, size : int) -> None:
        self.size = size
        self.chosen_weapon = None
        self.slots : list[Item | None] = [None] * size # this length should never change
        self.slots[0] = Item("twig")
    
    def is_full(self):
        """if all slots arent None, return True"""
        return all(self.slots)
    
    def receive_item(self, item : Item):
        print(f"\nYou recieved {item.name_in_sentence}\n{item.description}")

        item.parent_inventory = self

        if self.is_full():
            print("Your inventory is full!", end="\n"*2)
            action_options = [item for item in self.slots if item != None]
            action_idx = get_user_action_choice("Choose item to throw out: ", action_options)
            self.slots[action_idx] = item

        # set the first found empty slot to the received item
        else:
            # set the first found empty slot to the received item
            first_found_empty_slot_idx = self.slots.index(None)
            self.slots[first_found_empty_slot_idx] = item

    def remove_item(self, item : Item) -> None:
        item.parent_inventory = None
        self.slots.remove(item)

    def select_item(self) -> Item | None:
        items_in_inventory = [item for item in self.slots if item != None]

        print()
        if len(items_in_inventory):
            action_options = items_in_inventory + ["CANCEL"]
            action_idx = get_user_action_choice("Choose item to use: ", action_options)

            match action_options[action_idx]:
                case "CANCEL":
                    return None
                case _item:
                    return _item

        else:
            print("You have no items to use!")
            return None
    
    def __str__(self):
        lines = [
            "---------- [INVENTORY] ----------",
        ]

        for idx, item in enumerate(self.slots):
            lines.append(f"Slot {idx+1}: " + item.name if item != None else f"Slot {idx+1}: empty")
        
        return "\n".join(lines)

