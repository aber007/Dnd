from . import Log

class Effect:
    def __init__(self, type : str, effect : int, duration : int, target) -> None:
        self.type = type
        self.effect = effect
        self.duration = duration
        self.target = target
    
    def tick(self):
        self.target.take_damage(self.effect, "effect", log=False)
        self.duration -= 1

        Log.effect_tick(self.target.name, self.type, self.effect, self.duration)

        if self.duration == 0:
            self.target.active_effects.remove(self)
        