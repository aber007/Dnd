#This does not need to be in the final game, i was just bored

from . import CONSTANTS
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
except:
    os.system("pip install pygame")
    import pygame

# Initialize pygame mixer
pygame.mixer.init()

class music:

    def __init__(self, ambience_playlist):
        self.ambience_playlist = ["../story/ambience1.wav", "../story/fight.mp3"]

    def play(file_path):
        if CONSTANTS["music"]:
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

