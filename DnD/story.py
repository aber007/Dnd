#This does not need to be in the final game, i was just bored

import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
except:
    os.system("pip install pygame")
    import pygame

# Initialize pygame mixer
pygame.mixer.init()

def play(file_path):
    current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
    target_file = os.path.join(current_dir, '..', 'story', file_path)
    target_file = os.path.abspath(target_file)
    pygame.mixer.music.load(target_file)
    pygame.mixer.music.play(loops=-1)

def pause():
    pygame.mixer.music.pause()

def resume():
    pygame.mixer.music.unpause()

def stop():
    pygame.mixer.music.stop()

