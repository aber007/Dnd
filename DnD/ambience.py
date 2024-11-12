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
        self.ambience = ["../story/ambience1.mp3", "../story/ambience2.mp3"]
        self.replace_ambience = []
        self.fight = "../story/fight.mp3"


    def play(self, type):
        if CONSTANTS["music"]:
            match type:
                case "ambience":
                    file_path = choice(self.ambience)
                    if len(self.ambience) != 0:
                        self.replace_ambience.append(file_path)
                        self.ambience.pop(self.ambience.index(file_path))
                    else:
                        self.ambience = self.replace_ambience
                        self.replace_ambience.clear()
                case "fight":
                    file_path = choice(self.fight)

            current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
            target_file = os.path.join(current_dir, '..', 'story', file_path)
            target_file = os.path.abspath(target_file)
            pygame.mixer.music.load(target_file)
            pygame.mixer.music.play(loops=-1)

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
        pygame.mixer.music.fadeout()

