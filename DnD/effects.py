from . import Log

class Effect:
    def __init__(self, name : str, type : str, effect : int, effect_type : int, duration : int, target) -> None:
        """name : the name the logger should call this effect\n
        type : the type of effect this is, aka hp (heals) or dmg (deals dmg)\n
        effect : the potency of this Effect, aka amount of hp to heal or dmg to deal\n
        effect_type : if this Effect is of type dmg, when calling the target.take_damage pass this arg as the type param\n
        duration : how many rounds this effect should be active\n
        target : the entity this effect applies to"""

        self.name = name
        self.type = type
        self.effect = effect
        self.effect_type = effect_type
        self.duration = duration
        self.target = target
    
    def tick(self):
        self.duration -= 1

        match self.type:
            case "hp":
                self.target.heal(additional_hp=self.effect, log=False)
            case "dmg":
                self.target.take_damage(dmg=self.effect, dmg_type=self.effect_type, log=False)
        
        Log.effect_tick(self)
        
        if self.duration == 0:
            self.target.active_effects.remove(self)
    
    def force_expire(self) -> None:
        self.duration = 0

    def has_worn_off(self) -> bool:
        return self.duration == 0
