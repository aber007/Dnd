from . import CONSTANTS, Log, ANSI
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
        words = s.split(" ")
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

        self.text_discovered_color = ANSI.RGB(*CONSTANTS["lore_text_discovered_word_color"], "fg")
        self.text_undiscovered_color = ANSI.RGB(*CONSTANTS["lore_text_undiscovered_word_color"], "fg")

        # list of every word in the lore text. everything is encrypted
        with open(CONSTANTS["encrypted_lore_file"], "r") as f:
            self.encrypted_lore_words : list[str] = f.read().split(" ")
        
        # how many words to decode per discovered page
        self.lore_page_word_count = round(len(self.encrypted_lore_words) * CONSTANTS["lore_page_word_percent"])
        
        # list of every word in the lore text. if the user discovered a word then its not encrypted
        self.lore_words : list[str] = []

        self.load_discovered_lore()
        self.decrypt_already_discovered_lore()
    
    def load_discovered_lore(self):
        """Loads the user specific file where their lore progress is stored"""
        
        if os.path.exists(CONSTANTS["discovered_lore_file"]):
            with open(CONSTANTS["discovered_lore_file"], "r") as f:
                self.discovered_lore : list[bool] = json.load(f)
        
        else:
            self.discovered_lore = [False] * len(self.encrypted_lore_words)
            with open(CONSTANTS["discovered_lore_file"], "w") as f:
                json.dump(self.discovered_lore, f)
    
    def decrypt_already_discovered_lore(self):
        """Go through each bool in the discovered_lore list\n
        If true then the user has previously discovered that word, therefore decode it\n
        If false then the user hasnt discovered that word, therefore dont decode it\n
        Then add the word, decoded or not, to a list"""

        for idx,is_discovered in enumerate(self.discovered_lore):
            if is_discovered:
                word = Cipher.decode(self.encrypted_lore_words[idx], self.encryption_shift)
            else:
                word = self.encrypted_lore_words[idx]
            self.lore_words.append(word)

    def save_discovered_lore(self):
        """Saves the lore progress to a user specific file"""
        with open(CONSTANTS["discovered_lore_file"], "w") as f:
            json.dump(self.discovered_lore, f)

    def all_words_discovered(self) -> bool:
        return all(self.discovered_lore)

    def get_undiscovered_word_idxs(self) -> list[int]:
        """Returns the indexes of all undiscovered words"""
        return [idx for idx,is_discovered in enumerate(self.discovered_lore) if not is_discovered]

    def decode_word_at_idx(self, idx : int) -> None:
        self.lore_words[idx] = Cipher.decode(self.lore_words[idx], self.encryption_shift)
        self.discovered_lore[idx] = True

    def discovered_page(self) -> None:
        # the first time the player enters either a shop or a chest room the items are instantly generated
        # if all pages have been discovered then the genereated item cant be a page
        # if the player repeatedly enters a chest room, which load a page, doesnt open the chest and moves on
        #    there will eventually be more pages in unopened chests than lore
        #    if the player discoveres a page, despite all pages already being discovered, tell the player they found
        #    a page from an irrelevant letter

        if self.all_words_discovered():
            Log.found_irrelevant_lore_letter_page()
            return

        undiscovered_word_idxs : list[int] = self.get_undiscovered_word_idxs()

        # pick a random item from the undiscovered word indexes list
        # then remove the chosen index from the list of undiscovered word indexes
        # then decode the word at the chosen index and mark the word as discovered (doesnt write to file)
        # loop this 'self.lore_page_word_count' times or until the list of undiscovered word indexes is empty
        for _ in range(self.lore_page_word_count):
            chosen_word_idx = choice(undiscovered_word_idxs)
            undiscovered_word_idxs.remove(chosen_word_idx)
            
            self.decode_word_at_idx(chosen_word_idx)

            if len(undiscovered_word_idxs) == 0:
                break

        # since self.decode_word_at_idx is called multiple times and changes self.discovered_lore on every call
        # save the discovered lore to file once
        self.save_discovered_lore()

    def __str__(self) -> str:
        colored_words : list[str] = []
        for idx,is_discovered in enumerate(self.discovered_lore):
            appropriate_color = {True: self.text_discovered_color, False: self.text_undiscovered_color}[is_discovered]
            colored_words.append(appropriate_color + self.lore_words[idx] + ANSI.Color.off)
        
        return " ".join(colored_words)


Lore = _Lore()


if __name__ == "__main__":
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a bibendum leo. ttt sss"
    print(text)
    encoded = Cipher.encode(text, 7)
    print(encoded)
    decoded = Cipher.decode(encoded, 7)
    print(decoded)
