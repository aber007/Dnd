import os
import json
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
    test = "test"
    testsimple = "aaabbb cccddd..."
    shift = 7

    def encode(self, s : str, shift : int | None = None) -> str:
        """Pass shift to override the shift attribute stored in self"""

        if shift == None:
            shift = self.shift

        words = s.split()
        shifted_words = []

        for word in words:
            chars_in_word = list(word)
            shifted_chars = []

            # go through each character in the word and encrypt it
            for char in chars_in_word:
                # if the character isnt in the alphabet, eg. ".", dont modify it
                if char.lower() not in self.alphabet:
                    shifted_chars.append(char)
                    continue

                uppercase = is_upper(char)
                alph_idx = self.alphabet.index(char.lower())

                # the idx of the current character + shift
                # the resulting idx exceeding the length of self.alphabet is accounted for
                shifted_alph_idx = wrap(0, alph_idx + shift, len(self.alphabet))
                resulting_char = self.alphabet[shifted_alph_idx]
                resulting_char = resulting_char.upper() if uppercase else resulting_char

                shifted_chars.append(resulting_char)

            # merge all the encrypted characters into an encrypted word
            shifted_words.append("".join(shifted_chars))

        # merge all the encrypted words
        return " ".join(shifted_words)
    

    def decode(self, s : str) -> str:
        return self.encode(s = s, shift = -self.shift)

    
    def update_lore(self) -> None:
        """Updates a random non found part of the lore to be readable"""

        #Get location of files
        current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        lore_dir = os.path.abspath(os.path.join(current_dir, '..', 'story', 'lore_text', 'actual_lore.txt'))
        data = os.path.abspath(os.path.join(current_dir, '..', 'story', 'lore_text', 'pages.json'))

        #Find the individual parts of the lore
        with open(data, "r") as f:
            pages_data : dict = json.load(f)
        possible_notes = []
        for key in pages_data.keys():
            if pages_data[key] == False:
                possible_notes.append(key)
        if len(possible_notes) == 0:
            print("You have found all pieces of the letter")
            return None
        decryption_key = int(choice(possible_notes))
        print(f"You found piece {decryption_key}")

        #Update found notes
        pages_data[str(decryption_key)] = True
        with open(data, "w") as f:
            json.dump(pages_data, f)

        with open(lore_dir, "r") as file:
            lore = file.read()
        colon_indices = [i for i, char in enumerate(lore) if char == ":"]

        #Modify lines
        first_index = colon_indices[decryption_key-1]+1
        last_index = colon_indices[decryption_key]
        before = lore[:first_index]
        to_modify = lore[first_index:last_index]
        after = lore[last_index:]

        decrypted_lines= "\n".join(self.decoder(line) for line in to_modify.splitlines())
        new = before + decrypted_lines +"\n"+ after

        with open(lore_dir, "w") as lore_file:
            lore_file.write(new)

            
    


if __name__ == "__main__":
    
    cipher = Cipher()
    cipher.update_lore()


    # text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a bibendum leo. ttt sss"
    # print(text)
    # encoded = cipher.encode(text)
    # print(encoded)
    # decoded = cipher.decode(encoded)
    # print(decoded)
    
    # current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
    # lore_dir = os.path.abspath(os.path.join(current_dir, '..', 'story', 'lore_text', 'actual_lore.txt'))
    # with open(lore_dir, "r") as lore_file:
    #     lore_lines = lore_file.read().split("\n")
    # for line in lore_lines:
    #     if line != ":":
    #         print(cipher.encoder(line))
    #     else:
    #         print(":")
