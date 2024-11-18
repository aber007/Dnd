class Effect:
    def __init__(self, type : str, effect : int, duration : int, target) -> None:
        self.type = type
        self.effect = effect
        self.duration = duration
        self.target = target
    
    def tick(self):
        self.target.take_damage(self.effect, "effect")
        self.duration -= 1

        print(
            f"\nThe {self.target.name} was hurt for {self.effect} DMG from the {self.type} effect.",
            (f"Duration remaining: {self.duration}" if self.duration != 0 else f"The {self.type} effect wore off"),
            end="\n"*2)

        if self.duration == 0:
            self.target.active_effects.remove(self)
        