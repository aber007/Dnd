import time
from typing import Callable
from multiprocessing import Process, Manager

class Animation:
    def __init__(
            self,
            start_val : int | float,
            end_val : int | float,
            duration : int | float,
            on_val_update : Callable[[int | float], None],
            on_anim_finished : Callable[[int | float], None] | None = None
            ) -> None:
        
        self.start_val = start_val
        self.end_val = end_val
        self.val_delta = end_val - start_val
        self.duration = duration
        self.on_val_update = on_val_update
        self.on_anim_finished = on_anim_finished

        self.is_started = False
        self.is_finished = False
        self.start_time : float = None
    
    def start(self):
        self.start_time = time.time()
        self.is_started = True

    def update(self):
        percent_done = min(1, (time.time() - self.start_time)/self.duration)
        self.on_val_update(self.start_val + self.val_delta * percent_done)

        if percent_done == 1:
            self.is_finished = True
            if self.on_anim_finished != None:
                self.on_anim_finished(self.end_val)

class AnimationLibrary:
    def __init__(self) -> None:
        self.anims : list[Animation] = []
        self.has_active_animations : bool = False
    
    def add_anim(self, anim : Animation):
        self.anims.append(anim)

    def update_anims(self):
        self.has_active_animations = len(self.anims) and all(anim.is_started for anim in self.anims)

        for anim in self.anims:
            if anim.is_finished:
                self.anims.remove(anim)

            elif not anim.is_started:
                anim.start()

            else:
                anim.update()



if __name__ == "__main__":
    class ee:
        def __init__(self) -> None:
            self.v = 0

    e = ee()

    anim_lib = AnimationLibrary()
    anim_lib.add_anim(Animation(0, 1, 2, lambda v : setattr(e, "v", v)))

    while True:
        print(e.v)
        anim_lib.update_anims()
        time.sleep(1/5)