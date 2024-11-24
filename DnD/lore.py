from . import CONSTANTS, Log
import json, os
from random import choice


def is_upper(s : str) -> bool:
    """Returns bool wether the entire string is uppercase"""
    return s == s.upper()

def wrap(min_val : int, val : int, max_val : int) -> int:
    """Wraps val to be whin min_val (incl.) and max_val (excl.)\n
    Recursive wrapping is supported, meaning 0, -5, 2 -> 1 works\n
    0, 0, 6 -> 0\n
    0, -1, 6 -> 5\n
    0, -2, 6 -> 4\n
    0, 7, 6 -> 1\n
    0, 8, 6 -> 2"""

    if min_val <= val < max_val:
        return val
    
    elif max_val <= val:
        return wrap(min_val, val - max_val, max_val)
    
    elif val < min_val:
        return wrap(min_val, max_val - abs(val), max_val)

class Cipher:
    alphabet = list("abcdefghijklmnopqrstuvwxyz")

    def encode(s : str, shift : int) -> str:
        words = s.split()
        shifted_words = []

        for word in words:
            chars_in_word = list(word)
            shifted_chars = []

            # go through each character in the word and encrypt it
            for char in chars_in_word:
                # if the character isnt in the alphabet, eg. ".", dont modify it
                if char.lower() not in Cipher.alphabet:
                    shifted_chars.append(char)
                    continue

                uppercase = is_upper(char)
                alph_idx = Cipher.alphabet.index(char.lower())

                # the idx of the current character + shift
                # the resulting idx exceeding the length of self.alphabet is accounted for
                shifted_alph_idx = wrap(0, alph_idx + shift, len(Cipher.alphabet))
                resulting_char = Cipher.alphabet[shifted_alph_idx]
                
                if uppercase:
                    resulting_char = resulting_char.upper()

                shifted_chars.append(resulting_char)

            # merge all the encrypted characters into an encrypted word
            shifted_words.append("".join(shifted_chars))

        # merge all the encrypted words
        return " ".join(shifted_words)
    

    def decode(s : str, shift : int) -> str:
        return Cipher.encode(s = s, shift = -shift)


class _Lore:
    def __init__(self) -> None:
        # how far each character was shifted when encoding the lore
        self.encryption_shift = 7

        with open(CONSTANTS["encrypted_lore_file"], "r") as f:
            self.pages : dict[str, str] = json.loads(f.read())

        self.load_discovered_pages()
    
    def load_discovered_pages(self):
        """Loads the user specific file where their lore progress is stored"""
        
        if os.path.exists(CONSTANTS["discovered_pages_file"]):
            with open(CONSTANTS["discovered_pages_file"], "r") as f:
                self.discovered_pages = json.loads(f.read())
        
        else:
            self.discovered_pages = {str(page_idx) : False for page_idx in range(len(self.pages))}
            with open(CONSTANTS["discovered_pages_file"], "w") as f:
                json.dump(self.discovered_pages, f)
    
    def save_discovered_pages(self):
        """Saves the lore progress to a user specific file"""
        with open(CONSTANTS["discovered_pages_file"], "w") as f:
            json.dump(self.discovered_pages, f)

    def all_pages_discovered(self) -> bool:
        return all(self.discovered_pages.values())

    def get_undiscovered_pages(self) -> list[int]:
        return [page_idx for page_idx, discovered in self.discovered_pages.items() if not discovered]
    
    def discovered_page(self) -> None:
        # the first time the player enters either a shop or a chest room the items are instantly generated
        # if all pages have been discovered then the genereated item cant be a page
        # if the player repeatedly enters a chest room, which load a page, doesnt open the chest and moves on
        #    there will eventually be more pages in unopened chests than lore
        #    if the player discoveres a page, depsite all pages already being discovered, tell the player they found
        #    a page from an irrelevant letter

        if self.all_pages_discovered():
            Log.found_irrelevant_lore_letter_page()
            return
        
        page_idx = choice(self.get_undiscovered_pages())

        self.discovered_pages[page_idx] = True
        self.pages[page_idx] = Cipher.decode(self.pages[page_idx], self.encryption_shift)

        self.save_discovered_pages()
        Log.found_lore_letter_page(page_idx)
    
    def get_pages(self) -> list[str]:
        return self.pages.values()


Lore = _Lore()


if __name__ == "__main__":
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a bibendum leo. ttt sss"
    print(text)
    encoded = Cipher.encode(text, 7)
    print(encoded)
    decoded = Cipher.decode(encoded, 7)
    print(decoded)
