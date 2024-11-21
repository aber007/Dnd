class Effect:
    def __init__(self, type : str, effect : int, duration : int, target) -> None:
        self.type = type
        self.effect = effect
        self.duration = duration
        self.target = target
    
    def tick(self):
        from .main import Enemy

        self.target.take_damage(self.effect, "effect")
        self.duration -= 1

        print(
            f"\nThe {self.target.name if isinstance(self.target, Enemy) else 'player'} was hurt for {self.effect} DMG from the {self.type} effect.",
            (f"Duration remaining: {self.duration}" if self.duration != 0 else f"The {self.type} effect wore off"),
            end="\n"*2)

        if self.duration == 0:
            self.target.active_effects.remove(self)

class Buff:
    def __init__(self, type : str, effect : int, duration : int, target) -> None:
        self.target = target
        self.type = type
        self.effect = effect
        self.duration = duration
        self.getattr = f"self.target.{self.type}"
        setattr(target, type, eval(self.getattr)+effect)

    def tick(self):
        self.duration -= 1

        if self.duration == 0:
            print("The Buff has ran out")
            self.target.active_effects.remove(self)
            setattr(self.target, self.type, eval(self.getattr)-self.effect)
            

        
        
    

        