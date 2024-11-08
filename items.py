import main

class Item:
    def __init__(self, item_id) -> None:
        self.id = item_id

        # get the attributes of the given item_id and make them properties of this object
        [setattr(self, k, v) for k,v in main.items_data_dict[item_id].items()]
    
    def use(self, player : main.Player):
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
        return all(self.values())
    
    def receive_item(self, item : Item):
        if self.is_full():
            pass # choose item to throw out (could be the new item)

        else:
            for idx,slot in enumerate(self.slots):
                if slot == None:
                    self.slots[idx] = item
                    break
    
    def __str__(self):
        return "\n".join(
            "---------- [INVENTORY] ----------",
            "Equipped weapon slot contains " + self.equipped_weapon.display_name,
            *[f"Slot {idx} contains {item.display_name}" for idx,item in enumerate(self.slots)],
            )

