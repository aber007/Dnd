import math
from random import randint, uniform
from . import (
    CONSTANTS,
    ENEMY_DATA,
    SKILL_TREE_DATA,
    Item,
    Inventory,
    Vector2,
    get_user_action_choice,
    wait_for_key,
    ANSI,
    Effect,
    Log,
    )

class Entity:
    def take_damage(self, dmg : int, dmg_type : str = "melee", source : str = "", log : bool = True) -> int:
        """source is used to specify what caused the dmg. Only used if log == True"""
        if isinstance(self, Enemy) and dmg_type == "melee":    dmg = max(0, dmg - self.defence_melee)
        elif isinstance(self, Player) and dmg_type == "melee": dmg = max(0, dmg - self.defence)
        
        self.hp = max(0, self.hp - dmg)
        self.is_alive = 0 < self.hp
        
        if self.name == "player":
            self.stats["HP lost"] += dmg

        if log:
            Log.entity_took_dmg(self.name, dmg, self.hp, self.is_alive, source)
        
        return dmg

    def heal(self, additional_hp : int, log : bool = True):
        # cap the hp to max_hp
        hp_before = self.hp
        self.hp = min(self.hp + additional_hp, self.max_hp)
        hp_delta = self.hp - hp_before

        if log:
            Log.entity_healed(self.name, hp_before, additional_hp, hp_delta, self.hp)

        if self.name == "player":
            self.stats["HP gained"] += hp_delta

    def add_effect(self, name : str, type : str, effect : int, effect_type : str, duration : int, log : bool = True) -> Effect | None:
        """Instantiates the Effect class and adds it to this entity's list of current effects only if an effect of the same type isnt present\n
        Returns the Effect instance or None, depending on if the effect was successfully added\n
        The returend Effect instance is meant to be used with Enemy.special_is_active"""

        current_effect_types = [active_effect.type for active_effect in self.active_effects]

        # only add the effect if an effect of the same types isnt present
        if type not in current_effect_types:
            effect_instance = Effect(name=name, type=type, effect=effect, effect_type=effect_type, duration=duration, target=self)
            self.active_effects.append(effect_instance)
            if log:
                Log.entity_received_effect(effect_instance)
            
            return effect_instance
        
        else:
            Log.entity_received_already_present_effect(name)
    
    def clear_effects(self):
        for effect in self.active_effects:
            effect.force_expire()
        
        self.active_effects : list[Effect] = []
    
    def update_effects(self) -> int:
        """Returns the amount of effects that were ticked"""
        effects_ticked = 0

        # instance the self.active_effects list since effect.tick() might remove itself from the list
        for effect in list(self.active_effects):
            effect.tick()
            effects_ticked += 1
        
        return effects_ticked


class Player(Entity):
    def __init__(self, parent_map) -> None:
        self.parent_map : any = parent_map
        self.position : Vector2 = self.parent_map.starting_position
        self.name = "player"

        # combat related attributes
        self.is_alive = True
        self.hp = CONSTANTS["player_hp"]
        self.max_hp = CONSTANTS["player_max_hp"]
        self.defence = CONSTANTS["player_base_defence"]
        self.current_combat : any | None = None
        self.active_effects = []

        self.permanent_dmg_bonus = 0
        self.temp_dmg_factor = 1

        # Fix this later, these are just temporary
        self.stats = {
            "HP gained": 0,
            "HP lost": 0,
            "Gold earned": 0,
            "EXP gained": 0,
            "DMG dealt": 0,
            "Monsters defeated": 0
        }

        # progression related attributes
        self.inventory = Inventory(parent=self)
        self.skill_tree_progression = {"Special": 0, "HP": 0, "DMG": 0}
        self.skill_functions = {"before_attack": [], "after_attack": [], "new_non_combat_round": []}

        self.active_dice_effects : list[int] = []
    
    def get_dice_modifier(self) -> int:
        return sum(self.active_dice_effects)
    
    def roll_dice(self) -> tuple[bool,int] | int:
        """Roll the dice and include any dice modifiers. Return the result"""

        # get a random number between 1 and dice_sides then add the dice modifier
        # max() ensures the roll has a min value of 1
        dice_result = max(1, randint(1, CONSTANTS["dice_sides"]) + self.get_dice_modifier())
        self.active_dice_effects.clear()

        return dice_result

    def open_inventory(self) -> tuple[int, Item] | Item | None:
        """If any damage was dealt, return tuple[dmg, Item]\n
        If an item was used that didnt deal dmg, return Item\n
        If no item was used return None"""

        selected_item : Item | None = self.inventory.open()

        if selected_item == None:
            return None

        if selected_item.offensive:
            if self.current_combat == None:
                Log.use_combat_item_outside_combat()
                Log.newline()
                wait_for_key("[Press ENTER to continue]", "Return")

            else:
                dmg = selected_item.use()
                return dmg, selected_item

        else:
            # non offensive items always return a callable where the argument 'player' is expected
            use_callable = selected_item.use()
            use_callable(self)

        return selected_item
    
    def on_lvl_up(self):
        """Set the players bonus health and dmg based on the current lvl"""

        # health
        previous_max_hp = self.max_hp
        self.max_hp += math.floor(CONSTANTS["player_lvl_to_bonus_hp_additive_func"](self.inventory.lvl))
        max_hp_delta = self.max_hp - previous_max_hp
        Log.player_max_hp_increased(previous_max_hp, self.max_hp)

        self.heal(max_hp_delta) # heal the player for the new max hp

        # dmg
        previous_dmg_bonus = self.permanent_dmg_bonus
        self.permanent_dmg_bonus += CONSTANTS["player_lvl_to_bonus_dmg_additive_func"](self.inventory.lvl)
        Log.player_bonus_dmg_increased(previous_dmg_bonus, self.permanent_dmg_bonus)
    
    def _get_skill_tree_progression_options(self) -> tuple[list[int]]:
        branch_options_prefixes = []
        branch_options = []
        subtexts = []

        color_red = ANSI.RGB(*CONSTANTS["skill_tree_cross_color"], "bg")
        color_green = ANSI.RGB(*CONSTANTS["skill_tree_check_color"], "bg")
        color_off = ANSI.Color.off

        # go through all branches and add them as an option if available
        for branch_name, stages in SKILL_TREE_DATA.items():
            # handle Impermanent perks separately
            if branch_name == "Impermanent": continue

            lvls_in_branch : int = len(stages)
            player_progression_in_branch : int = self.skill_tree_progression[branch_name]

            # if the branch isnt already completed
            if player_progression_in_branch + 1 <= lvls_in_branch:
                next_lvl_dict = stages[str(player_progression_in_branch+1)]

                # branch_progression_str is a comprised of a few colored boxes representing the players progression in this branch
                branch_progression_str = color_off + str(f"{color_green} {color_off}"*player_progression_in_branch) + str(f"{color_red} {color_off}"*(lvls_in_branch-player_progression_in_branch)) + color_off + " "

                branch_options_prefixes.append(branch_progression_str)
                branch_options.append(f"{branch_name} - {next_lvl_dict['name']}")
                subtexts.append(f"{' '*6}{next_lvl_dict['description']}")
        
        # add the Impermanent perks
        for branch_name, skill_dict in SKILL_TREE_DATA["Impermanent"].items():
            branch_options_prefixes.append("")
            branch_options.append(f"Impermanent - {skill_dict['name']}")
            subtexts.append(f"{' '*6}{skill_dict['description']}")
        
        return branch_options_prefixes, branch_options, subtexts

    def receive_skill_point(self, new_skill_points : int):
        wait_for_key(f"\nYou have {new_skill_points} unspent skill points!\n\n[Press ENTER to progress the skill tree]", "Return")

        for _ in range(new_skill_points):
            Log.clear_console()
            Log.header("SPEND SKILL POINTS", 1)

            branch_options_prefixes, branch_options, subtexts = self._get_skill_tree_progression_options()
            branch_option_idx = get_user_action_choice("Choose branch to progress in: ", action_options=branch_options, action_options_prefixes=branch_options_prefixes, subtexts=subtexts)

            # "Special - Syphon" -> "Special", "Syphon"
            branch_name_w_colored_bars, skill_name = branch_options[branch_option_idx].split(" - ", 1)
            branch_name = branch_name_w_colored_bars.split(ANSI.Color.off, 1)[0]
            match branch_name:
                case "Impermanent":
                    skill_name = skill_name.split(" ", 1)[0] # "HP boost" -> "HP"
                    skill_func = eval(SKILL_TREE_DATA[branch_name][skill_name]["func"])
                    skill_func({"player": self})

                case _:
                    branch_progression = self.skill_tree_progression[branch_name]
                    skill_dict = SKILL_TREE_DATA[branch_name][str(branch_progression+1)]
                    skill_func = eval(skill_dict["func"])
                    
                    if skill_dict["trigger_when"] == "now":
                        skill_func({"player": self})
                    else:
                        skill_func.return_val_type = skill_dict["return_val"]
                        self.skill_functions[skill_dict["trigger_when"]].append(skill_func)
                    
                    self.skill_tree_progression[branch_name] += 1
    
    def call_skill_functions(self, when : str, variables : dict[str,any]) -> list[any]:
        return_vars = []
        for func in self.skill_functions[when]:
            return_vars.append( {"val": func(variables), "return_val_type": func.return_val_type} )
        
        return return_vars


        
class Enemy(Entity):
    def __init__(self, enemy_type : str) -> None:
        # get the attributes of the given enemy_type and make them properties of this object
        # since the probability value won't be useful it's not added as an attribute
        [setattr(self, k, v) for k,v in ENEMY_DATA[enemy_type].items() if k != "probability"]

        self.is_alive = True
        self.active_effects = []

        # the effect object that was used when this enemy last used its special ability
        # its used to check wether the special ability is still in effect when deciding
        #   if the special ability should trigger again
        self.active_special_effect : Effect | None = None
    
    def attack(self, target : Entity, dmg_multiplier : int = 1, hide_source : bool = False) -> int:
        """Attack target with base damage * dmg_multiplier. Use hide_source to stop the take_damage log call from displaying source. The damage dealt is returned"""
        source = self.name if not hide_source else ""
        return target.take_damage(math.ceil(self.dmg * dmg_multiplier), source=source)
    
    def use_special(self, player : Player) -> None:
        """Runs the code for special abilities which can be used during combat"""

        Log.newline()
        Log.enemy_used_special(self.special_info)

        match self.special:
            case "trap":
                player.take_damage(dmg=self.special_dmg, dmg_type="trap", source=f"{self.name} trap")
            case "berserk":
                self.active_special_effect = player.add_effect(name="berserk", type="dmg", effect=self.dmg, effect_type="melee", duration=5, log=False)
            case "poison":
                self.active_special_effect = player.add_effect(name="poison", type="dmg", effect=2, effect_type="effect", duration=7, log=False)
            case "fire_breath":
                player.take_damage(dmg=self.special_dmg, dmg_type="magic", source=f"{self.name}'s fire breath")
            case "stone_skin":
                self.heal(round(self.max_hp * 0.1))
                self.active_special_effect = self.add_effect(name="stone skin", type="hp", effect=3, effect_type="", duration=3, log=False)
    
    def special_is_active(self) -> bool:
        """Returns wether the last used special attack is still in effect"""

        if self.active_special_effect == None:
            return False
        
        return not self.active_special_effect.has_worn_off()
