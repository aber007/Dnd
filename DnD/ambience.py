#This does not need to be in the final game, i was just bored

from . import CONSTANTS, Slider
from random import shuffle
import os, math
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
except:
    os.system("pip install pygame")
    import pygame

# Initialize pygame mixer
pygame.mixer.init()

class _Music:

    def __init__(self):
        self.ambience_playlist = ["ambience1.mp3", "ambience2.mp3", "ambience3maybe.mp3", "ambience4.mp3", "ambience5.mp3"] ; shuffle(self.ambience_playlist)
        self.fight_playlist = ["fight.mp3"] ; shuffle(self.fight_playlist)
        self.shop_playlist = ["shop_music.mp3"] ; shuffle(self.shop_playlist)

        self.current_song = ""
        self.current_song_type = ""

        self.current_dir = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
        self.music_dir = os.path.abspath(os.path.join(self.current_dir, "..", "story", "music"))

        pygame.mixer.music.set_volume(CONSTANTS["default_music_volume"])

  
    def change_volume(self):
        if not CONSTANTS["music_enabled"]:
            return
        
        if self.current_song == "":
            self.play("ambience")

        # the +1 adds a step where the volume is 0
        slider_steps = round(1 / CONSTANTS["music_slider_step_volume_percent"]) + 1
        slider_on_value_changed = lambda val : pygame.mixer.music.set_volume(max(0, (val/(slider_steps-1)) * CONSTANTS["music_max_volume_percent"]))
        Slider(
            length=slider_steps,
            on_value_changed=slider_on_value_changed,
            header="Choose music volume",
            starting_x=math.ceil((pygame.mixer.music.get_volume()*(slider_steps-1))/CONSTANTS["music_max_volume_percent"])
            ).start()


    def choose_song(self, new_song_type : str) -> str:
        previous_song = self.current_song
        new_song_type_playlist = getattr(self, f"{new_song_type}_playlist")

        # if the previous song is of the same type as the new song being chosen AND the previous song isnt the last song in the playlist:
        #   play the next song
        if previous_song in new_song_type_playlist and previous_song != new_song_type_playlist[-1]:
            current_song_idx = new_song_type_playlist.index(previous_song)
            file_name = new_song_type_playlist[current_song_idx+1]

        # otherwise if the previous song isnt of the same type as the new song being chosen OR we've ran out of songs:
        #   shuffle the playlist and play the first one
        else:
            shuffle(new_song_type_playlist)
            file_name = new_song_type_playlist[0]
        
        return os.path.join(self.music_dir, file_name)


    def play(self, new_song_type : str, force : bool = False):
        if not CONSTANTS["music_enabled"]:
            return
        
        # dont play a song if a song if that type is already playing, unless force == True
        if new_song_type == self.current_song_type and not force:
            return

        pygame.mixer.music.unload()

        file_path = self.choose_song(new_song_type)
        pygame.mixer.music.load(file_path)

        if new_song_type == "ambience":
            pygame.mixer.music.play(loops=0)
        else:
            pygame.mixer.music.play(loops=-1)
        
        self.current_song = file_path
        self.current_song_type = new_song_type

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()
    
    def get_current_song(self):
        return self.current_song

Music = _Music()