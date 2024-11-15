#This does not need to be in the final game, i was just bored

from . import CONSTANTS, Slider
from random import shuffle
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

    def __init__(self): # "ambience2.mp3", 
        self.ambience = ["ambience1.mp3", "ambience3maybe.mp3", "ambience4.mp3", "ambience5.mp3"] ; shuffle(self.ambience)
        self.fight = "fight.mp3"
        self.shop = "shop_music.mp3"
        self.file_path = ""
        self.current_song = ""

        self.current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        self.story_dir = os.path.abspath(os.path.join(self.current_dir, '..', 'story'))

        if CONSTANTS["music_enabled"]:
            pygame.mixer.music.set_volume(0)
            self.play("ambience")

            # the +1 adds a step where the volume is 0
            slider_steps = round(1 / CONSTANTS["music_slider_step_volume_percent"]) + 1
            slider_on_value_changed = lambda val : pygame.mixer.music.set_volume(max(0, val/slider_steps * CONSTANTS["music_max_volume_percent"]))
            Slider(slider_steps, slider_on_value_changed, header="Choose music volume").start()


    def start_auto_queue():
        pass

    def play(self, type):
        if not CONSTANTS["music_enabled"]:
            return
        
        match type:
            case "ambience":
                # if the current song is of type ambience AND the current song isnt the last song in the ambience list:
                #   play the next song
                if self.current_song in self.ambience and self.current_song != self.ambience[-1]:
                    current_song_idx = self.ambience.index(self.current_song)
                    self.file_path = self.ambience[current_song_idx+1]

                # otherwise if the current song isnt of type ambience OR we've ran out of songs:
                #   reshuffle the song list and play the first one
                else:
                    shuffle(self.ambience)
                    self.file_path = self.ambience[0]
            
            case "fight":
                self.file_path = self.fight
            
            case "shop":
                self.file_path = self.shop

        
        target_file = os.path.join(self.story_dir, self.file_path)
        pygame.mixer.music.load(target_file)

        if type == "ambience":
            pygame.mixer.music.play(loops=0, fade_ms=500)
        else:
            pygame.mixer.music.play(loops=-1, fade_ms=500)
        
        self.current_song = self.file_path

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

