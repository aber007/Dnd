from . import ITEM_DATA, get_user_action_choice

class Item:
    def __init__(self, item_id : str) -> None:
        self.id = item_id
        self.parent_inventory : Inventory | None = None

        # get the attributes of the given item_id and make them properties of this object
        [setattr(self, k, v) for k,v in ITEM_DATA[item_id].items()]
    
    def use(self) -> any:
        """If the item is offensive, return its damage\n
        If the item isnt offensive return a callable requiring 1 argument, player. This callable is expected to called in main"""
        # remember item durability

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
                        pass
                    
                    case "breath_of_life":
                        return_val = lambda player: player.heal(self.effect)
                    
                    case "breath_of_fire":
                        return_val = self.effect
                    
        
        self.durability -= 1
        if self.durability == 0:
            self.parent_inventory.remove_item(self)
        
        return return_val

    
    def __str__(self):
        return self.id



class Inventory:
    def __init__(self, size : int) -> None:
        self.size = size
        self.equipped_weapon = Item("twig")
        self.slots : list[Item | None] = [None] * size # this length should never change
    
    def is_full(self):
        """if all slots arent None, return True"""
        return all(self.slots)
    
    def receive_item(self, item : Item):
        print(f"\nYou recieved {item.name_in_sentence}\n{item.description}")

        item.parent_inventory = self

        if self.is_full():
            print("Your inventory is full!", end="\n"*2)
            action_options = [item for item in self.slots if item != None]
            action_nr = get_user_action_choice("Choose item to throw out: ", action_options)
            self.slots[int(action_nr)-1] = item

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
            action_nr = get_user_action_choice("Choose item to use: ", action_options)

            match action_options[int(action_nr)-1]:
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
            "Equipped weapon: " + self.equipped_weapon.name,
        ]

        for idx, item in enumerate(self.slots):
            lines.append(f"Slot {idx+1}: " + item.name if item != None else "")
        
        return "\n".join(lines)

