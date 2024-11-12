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
        self.ambience = ["ambience1.mp3", "ambience2.mp3"]
        self.replace_ambience = []
        self.fight = "fight.mp3"
        self.shop = "Shop_music.mp3"
        self.file_path = ""


    def play(self, type):
        if CONSTANTS["music"]:
            match type:
                case "ambience":
                    self.file_path = choice(self.ambience)
                    if len(self.ambience) != 0:
                        self.replace_ambience.append(self.file_path)
                        self.ambience.pop(self.ambience.index(self.file_path))
                    else:
                        self.ambience = self.replace_ambience
                        self.replace_ambience.clear()
                case "fight":
                    self.file_path = self.fight
                case "shop":
                    self.file_path = self.shop

            current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
            target_file = os.path.join(current_dir, '..', 'story', self.file_path)
            target_file = os.path.abspath(target_file)
            pygame.mixer.music.load(target_file)
            pygame.mixer.music.play(loops=-1, fade_ms=500)

    def nexttrack(self):
        global index
        index += 1
        if index >= len(self.ambience_playlist):
            index = 0
        pygame.mixer.music.load(self.ambience_playlist[index])
        pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def fadeout(self):
        pygame.mixer.music.fadeout(200)

