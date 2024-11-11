from . import ITEM_DATA, get_user_action_choice

class Item:
    def __init__(self, item_id : str) -> None:
        """Item(item_id, items_data_dict[item_id])"""

        self.id = item_id

        # get the attributes of the given item_id and make them properties of this object
        [setattr(self, k, v) for k,v in ITEM_DATA[item_id].items()]
    
    def use(self, player):
        # remember item durability
        match self.type:
            case "weapon":
                pass
    
            case "potion":
                if self.affects == "dice":
                    player.active_dice_effects.append(self.effect)
            
            case "spell":
                pass #custom code for each spell
    
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

        if self.is_full():
            print("Your inventory is full!", end="\n"*2)
            action_options = [item for item in self.slots if item != None]
            action_nr = get_user_action_choice("Choose item to throw out: ", action_options)
            self.slots[int(action_nr)-1] = None

        print(f"\nYou recieved {item.name_in_sentence}")

        # set the first found empty slot to the received item
        for idx,slot in enumerate(self.slots):
            if slot == None:
                self.slots[idx] = item
                break

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
            lines.append(f"Slot {idx+1}: " + item.name if item != None else "empty")
        
        return "\n".join(lines)

