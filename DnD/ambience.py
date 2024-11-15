#This does not need to be in the final game, i was just bored

from . import CONSTANTS
from random import choice
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
except:
    os.system("pip install pygame")
    import pygame

# Initialize pygame mixer
pygame.mixer.init()

class Music:

    def __init__(self):
        self.ambience = ["ambience1.mp3", "ambience2.mp3", "ambience3maybe.mp3", "ambience4.mp3", "ambience5.mp3"]
        self.replace_ambience = []
        self.fight = "fight.mp3"
        self.shop = "shop_music.mp3"
        self.file_path = ""
        self.current_song = ""


        pygame.mixer.music.set_volume(0)
        self.play("ambience")

        # the +1 adds a step where the volume is 0
        slider_steps = round(1 / CONSTANTS["music_slider_step_volume_percent"]) + 1
        slider_on_value_changed = lambda val : pygame.mixer.music.set_volume(max(0, val/slider_steps * CONSTANTS["music_max_volume_percent"]))
        Slider(slider_steps, slider_on_value_changed, header="Choose music volume").start()


    def play(self, type):
        if CONSTANTS["music"]:
            match type:
                case "ambience":
                    if len(self.ambience) != 0:
                        self.file_path = choice(self.ambience)
                        self.replace_ambience.append(self.file_path)
                        self.ambience.pop(self.ambience.index(self.file_path))
                    else:
                        self.ambience = self.replace_ambience.copy()
                        self.replace_ambience.clear()
                        self.file_path = choice(self.ambience)
                        self.replace_ambience.append(self.file_path)
                        self.ambience.pop(self.ambience.index(self.file_path))
                case "fight":
                    self.file_path = self.fight
                case "shop":
                    self.file_path = self.shop

            current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
            target_file = os.path.join(current_dir, '..', 'story', self.file_path)
            target_file = os.path.abspath(target_file)
            pygame.mixer.music.load(target_file)
            if type == "ambience":
                pygame.mixer.music.play(loops=0, fade_ms=500)
                self.nexttrack()
            else:
                pygame.mixer.music.play(loops=-1, fade_ms=500)
            self.current_song = self.file_path

    def nexttrack(self):
        if len(self.ambience) != 0:
            self.file_path = choice(self.ambience)
            self.replace_ambience.append(self.file_path)
            self.ambience.pop(self.ambience.index(self.file_path))
        else:
            self.ambience = self.replace_ambience.copy()
            self.replace_ambience.clear()
            self.file_path = choice(self.ambience)
            self.replace_ambience.append(self.file_path)
            self.ambience.pop(self.ambience.index(self.file_path))

        current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        target_file = os.path.join(current_dir, '..', 'story', self.file_path)
        target_file = os.path.abspath(target_file)

        pygame.mixer.music.queue(target_file)

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def fadeout(self):
        pygame.mixer.music.fadeout(200)

    def get_current_song(self):
        return self.current_song

