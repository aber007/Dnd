from . import ITEM_DATA

class Item:
    def __init__(self, item_id : str) -> None:
        """Item(item_id, items_data_dict[item_id])"""

        self.id = item_id

        # get the attributes of the given item_id and make them properties of this object
        [setattr(self, k, v) for k,v in ITEM_DATA[item_id].items()]
    
    def use(self, player):
        match self.type:
            case "weapon":
                player.current_enemy.take_damage(self.dmg)
        
            case "potion":
                if self.affects == "dice":
                    player.active_dice_effects.append(self.effect)
            
            case "spell":
                pass #custom code for each spell



class Inventory:
    def __init__(self, size : int) -> None:
        self.size = size
        self.equipped_weapon = Item("twig")
        self.slots : list[Item | None] = [None] * size
    
    def is_full(self):
        """if all slots arent None, return True"""
        return False
    
    def receive_item(self, item : str):

        if self.is_full():
            print(f"Choose what item to swap out for {Item(item).name}")
            print(Inventory)
            print(f"{self.size}) Leave item behind")

        else:
            print(f"You recieved {Item(item).name_in_sentence}")
            for idx,slot in enumerate(self.slots):
                if slot == None:
                    self.slots[idx] = item
                    break
    
    def __str__(self):
        lines = []
        lines.append("---------- [INVENTORY] ----------")
        lines.append("0) Equipped weapon slot contains " + self.equipped_weapon.name)

        for idx, item in enumerate(self.slots):
            print(idx, item)
            try:
                lines.append(f"Slot {idx+1} contains {Item(item).name}")
            except KeyError:
                lines.append(f"Slot {idx+1} is empty")

        
        return "\n".join(lines)

