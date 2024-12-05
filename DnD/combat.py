
from random import choices, choice, uniform
from time import sleep
from . import (
    CONSTANTS,
    ENEMY_DATA,
    Music,
    ANSI,
    Bar,
    combat_bar,
    DodgeEnemyAttack,
    wait_for_key,
    Log,
    Console,
    get_user_action_choice,
    Player,
    Enemy
    )

class Combat:
    def __init__(self, player : Player, map : any, force_enemy_type : str | None = None) -> None:
        self.player : Player = player
        self.map : any = map
        self.enemy : Enemy = self.create_enemy(force_enemy_type, player)
        self.turn = 0

    def create_enemy(self, force_enemy_type : str | None, player) -> Enemy:
        """Decide enemy type to spawn, then return enemy object with the attributes of said enemy type"""

        # needed for mimic traps
        if force_enemy_type:
            return Enemy(enemy_type = force_enemy_type)


        enemy_types = list(ENEMY_DATA.keys())

        spawn_probabilities : dict[str, float | int] = {}
        for enemy_type in enemy_types:
            # if an enemy's probability is -1 it should only be spawned using force_enemy_type
            if (enemy_probability := ENEMY_DATA[enemy_type]["probability"]) != -1:
                spawn_probabilities[enemy_type] = enemy_probability

        distace_from_spawn = ((abs(self.map.starting_position.x - self.player.position.x)**2) + (abs(self.map.starting_position.y - self.player.position.y)**2))**0.5
        for enemy_type in enemy_types:     
            if ENEMY_DATA[enemy_type]["probability"] == 0:
                last_probability = spawn_probabilities[enemy_type]
                new_probability = distace_from_spawn/10 * ((100-ENEMY_DATA[enemy_type]["exp"])/1000 + ((player.inventory.get_lvl()**0.9)/50))
                spawn_probabilities[enemy_type] += new_probability
            elif ENEMY_DATA[enemy_type]["probability"] > 0:
                last_probability = spawn_probabilities[enemy_type]
                new_probability = max(0, distace_from_spawn/10 * ((100-ENEMY_DATA[enemy_type]["exp"])/1000 + ((player.inventory.get_lvl()**0.9)/20)))
                spawn_probabilities[enemy_type] -= new_probability
                if spawn_probabilities[enemy_type] < 0: #For some reasion the probability can go below 0
                    spawn_probabilities[enemy_type] = 0
            if CONSTANTS["debug"]["show_enemy_probabilities"] and ENEMY_DATA[enemy_type]["probability"] >= 0:
                print(str(ENEMY_DATA[enemy_type]["name"]) + ": " + str(round(spawn_probabilities[enemy_type], 5)) + " : " + str(round(spawn_probabilities[enemy_type]-last_probability, 5))) #Not using fstring because of formatting issues


        enemy_type_to_spawn = choices(list(spawn_probabilities.keys()), list(spawn_probabilities.values()))[0]

        return Enemy(enemy_type = enemy_type_to_spawn)

    def start(self) -> None:
        self.player.current_combat = self
        self.player.clear_effects()

        Music.play("fight")

        Log.combat_enemy_revealed(self.enemy.name_in_sentence)
        Log.newline()

        wait_for_key("[Press ENTER to continue]", "Return")
        Log.clear_console()
        
        Log.header("COMBAT", 1)
        Console.save_cursor_position("combat round start")
        sleep(1)

        enemyturn = choice([True, False])

        
        fled = False
        while self.player.is_alive and self.enemy.is_alive and not fled:
            self.turn += 1

            Log.header(f"Turn {self.turn}", 2)

            someone_died = not self.update_effects()
            if someone_died:
                break

            self.write_hp_bars()

            if not enemyturn:
                fled = self.player_turn()
            else:
                self.enemy_turn()

            Log.newline()
            wait_for_key("[Press ENTER to continue]", "Return")
            Console.truncate("combat round start")
            
            enemyturn = not enemyturn
        

        Log.clear_console()
        Log.header("COMBAT COMPLETED", 1)

        # if the combat ended with the player alive and the enemy dead: mark the room as cleared
        if self.player.is_alive and not self.enemy.is_alive:
            Log.enemy_defeated(self.enemy.name, self.enemy.gold, self.enemy.exp)

            self.map.get_room(self.player.position).is_cleared = True

            self.player.inventory.gold += self.enemy.gold
            self.player.inventory.exp += self.enemy.exp

            # if the player lvld up .update_lvl() would call wait_for_key
            # if the player didnt lvl up then call wait_for_key here
            Log.newline()
            player_lvld_up = self.player.inventory.update_lvl()

            if not player_lvld_up:
                Log.newline()
                wait_for_key("[Press ENTER to continue]", "Return")

            self.player.stats["Gold earned"] += self.enemy.gold
            self.player.stats["EXP gained"] += self.enemy.exp
            self.player.stats["Monsters defeated"] += 1
        
        elif not fled:
            Log.combat_player_died()
            Log.newline()
            wait_for_key("[Press ENTER to continue]", "Return")
            

        self.player.temp_dmg_factor = CONSTANTS["player_default_temp_dmg_factor"]
        self.player.current_combat = None
        Music.play("ambience")

    def update_effects(self) -> bool:
        """Returns wether both the player and the enemy survived"""

        effects_ticked = self.enemy.update_effects()
        effects_ticked += self.player.update_effects()
        if 0 < effects_ticked:
            Log.newline()
        
        return self.player.is_alive and self.enemy.is_alive

    def write_hp_bars(self):
        # Figure out which prefix is longer then make sure the shorter one gets padding to compensate
        enemy_bar_prefix = f"{self.enemy.name} hp: {self.enemy.hp}   "
        player_bar_prefix = f"Player hp: {self.player.hp}   "
        longer_prefix = sorted([enemy_bar_prefix, player_bar_prefix], key=lambda i : len(i), reverse=True)[0]

        enemy_bar_prefix = enemy_bar_prefix.ljust(len(longer_prefix), " ")
        player_bar_prefix = player_bar_prefix.ljust(len(longer_prefix), " ")

        # Make sure the side with more hp has the longest health bar allowed
        #   and that the side with less hp has a health bar proportionate to the hp ratio
        #   eg. player hp 10, enemy hp 1 -> player bar length = max, enemy bar length = max * 0.1
        max_hp_ratio = self.enemy.max_hp / self.player.max_hp
        if max_hp_ratio <= 1:
            # player has more hp or equal
            player_bar_length = CONSTANTS["hp_bar_max_length"]
            enemy_bar_length = round(CONSTANTS["hp_bar_max_length"] * max_hp_ratio)
        else:
            enemy_bar_length = CONSTANTS["hp_bar_max_length"]
            player_bar_length = round(CONSTANTS["hp_bar_max_length"] * (1/max_hp_ratio))

        # Write the health bars to terminal
        Bar(
            length=player_bar_length,
            val=self.player.hp,
            min_val=0,
            max_val=self.player.max_hp,
            fill_color=ANSI.RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=player_bar_prefix
        )
        Bar(
            length=enemy_bar_length,
            val=self.enemy.hp,
            min_val=0,
            max_val=self.enemy.max_hp,
            fill_color=ANSI.RGB(*CONSTANTS["hp_bar_fill_color"], ground="bg"),
            prefix=enemy_bar_prefix
        )
        Log.newline()

    def player_turn(self) -> bool:
        """If the player attempted to flee: return the result, otherwise False"""

        Console.save_cursor_position("player turn start")

        fled = False
        action_completed = False  # Loop control variable to retry actions
        while not action_completed:
            action_options = ["Use item / Attack", "Attempt to Flee", "Surrender"]
            action_idx = get_user_action_choice("Choose action: ", action_options)

            Console.truncate("player turn start")
            match action_options[action_idx]:
                case "Use item / Attack":
                    action_completed = self.player_use_item_attack()
                    if action_completed:
                        return fled

                case "Attempt to Flee":
                    return self.player_attempt_to_flee()
                
                case "Surrender":
                    return self.player_surrender()

        
        return fled

    def player_use_item_attack(self) -> bool:
        """Returns wether the player sucessfully used an item or not, aka action_completed"""
        action_completed = False

        # item_return is either tuple[dmg done, item] or Item or None
        item_return = self.player.open_inventory()
        
        if isinstance(item_return, tuple):
            dmg, item = item_return
            dmg += self.player.permanent_dmg_bonus

            dmg_mod = combat_bar()
            dmg_factor = {"miss": 0, "hit": 1, "hit_x2": 2}[dmg_mod]

            Log.combat_player_attack_mod(dmg_factor, self.enemy.name, item.name_in_sentence)
            Log.newline()

            # if the player missed the enemy mark this turn as completed
            if dmg_factor == 0:
                return True

            # activate all the skills that are supposed to be ran before the attack fires
            return_vars = self.player.call_skill_functions(
                when="before_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg"])
            dmg = returned_dmg if len(return_vars) and returned_dmg != 0 else dmg

            dmg *= dmg_factor * self.player.temp_dmg_factor

            self.player.stats["DMG dealt"] += round(dmg)

            if CONSTANTS["debug"]["player_infinite_dmg"]:
                dmg = 10**6

            self.enemy.take_damage(round(dmg))

            # activate all the skills that are supposed to be ran after the attack fires
            return_vars = self.player.call_skill_functions(
                when="after_attack",
                variables={"player": self.player, "enemy": self.enemy, "dmg": dmg}
                )
            returned_dmg_done = sum([return_var["val"] for return_var in return_vars if return_var["return_val_type"] == "dmg_done" and return_var["val"] != None])
            if 0 < returned_dmg_done:
                Log.newline()
                Log.player_skill_damaged_enemy(self.enemy.name, returned_dmg_done)

            action_completed = True

        return action_completed

    def player_attempt_to_flee(self) -> bool:
        """Returns wether the attempt to flee was successful"""
        fled = False
        
        Log.combat_init_flee_roll()

        wait_for_key("[Press ENTER to roll dice]", "Return")
        roll = self.player.roll_dice()
        
        Log.clear_line()
        Log.combat_flee_roll_results(roll)
        Log.newline()

        # if you managed to escape
        if CONSTANTS["flee_min_roll_to_escape"] <= roll:
            # if the enemy hit you on your way out
            if roll < CONSTANTS["flee_min_roll_to_escape_unharmed"]:
                Log.enemy_attack_while_fleeing(self.enemy.name)
                self.enemy.attack(target=self.player)
                Log.newline()
                return True
            
            # if you escaped with coins
            elif CONSTANTS["flee_exact_roll_to_escape_coins"] <= roll:
                Log.combat_perfect_flee()
                Log.newline()
                gold_earned = round(self.enemy.gold * CONSTANTS["flee_20_coins_to_receive_factor"])
                self.player.inventory.gold += gold_earned
                self.player.stats["Gold earned"] += gold_earned
            
            Log.combat_flee_successful()
            fled = True

        # if you didnt escape
        else:
            Log.enemy_attack_unsuccessful_flee(self.enemy.name)
            self.enemy.attack(target=self.player, dmg_multiplier=2, hide_source=True)

        return fled
    
    def player_surrender(self) -> None:
        Log.combat_player_surrender()
        self.player.take_damage(dmg=self.player.hp, dmg_type="raw", source=self.enemy.name, log=True)
    

    def enemy_turn(self):
        dmg_factor = DodgeEnemyAttack().start()
        
        Log.newline()
        Log.enemy_attack(self.enemy.name)
        self.enemy.attack(target=self.player, dmg_multiplier=dmg_factor)

        if self.player.is_alive and not self.enemy.special_is_active() and uniform(0, 1) < self.enemy.special_chance:
            self.enemy.use_special(player=self.player)
