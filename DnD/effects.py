from . import Log

class Effect:
    def __init__(self, type : str, effect : int, duration : int, target) -> None:
        self.type = type
        self.effect = effect
        self.duration = duration
        self.target = target
    
    def tick(self):
        from .main import Enemy

        self.target.take_damage(self.effect, "effect") # log=False ?
        self.duration -= 1

        #TODO Log.effect_tick(self.target.name, self.type, self.effect, self.duration)
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
            try:
                self.target.active_effects.remove(self)
                setattr(self.target, self.type, eval(self.getattr)-self.effect)
            except ValueError:
                pass
                #This code will sometimes run twice and will therefore already remove the buff

            

        
        
    

        