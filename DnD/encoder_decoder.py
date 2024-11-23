import os
import json
from random import choice
class Cipher:
    alphabet = list("abcdefghijklmnopqrstuvwxyz")
    test = "test"
    testsimple = "aaabbb cccddd..."
    shift = 7

    def encoder(self, str : str):
        words = str.split()
        for word in range(len(words)):
            string = list(words[word])

            for i in range(len(string)):
                try:
                    try:
                        letterpos = self.alphabet.index(string[i])
                        uppercase = False
                    except ValueError:
                        letterpos = self.alphabet.index(string[i].lower())
                        uppercase = True

                    if letterpos + self.shift >= len(self.alphabet):
                        if uppercase:
                            string[i] = self.alphabet[letterpos + self.shift - len(self.alphabet)].upper()
                        else:
                            string[i] = self.alphabet[letterpos + self.shift - len(self.alphabet)]
                    else:
                        if uppercase:
                            string[i] = self.alphabet[letterpos + self.shift].upper()
                        else:
                            string[i] = self.alphabet[letterpos + self.shift]
                except ValueError:
                    string[i] = string[i]
                
                uppercase = False

            words[word] = "".join(string)

        return " ".join(words)
    

    def decoder(self, str : str):
        words = str.split()
        for word in range(len(words)):
            string = list(words[word])

            for i in range(len(string)):
                try:
                    try:
                        letterpos = self.alphabet.index(string[i])
                        uppercase = False
                    except:
                        letterpos = self.alphabet.index(string[i].lower())
                        uppercase = True

                    if letterpos - self.shift < 0:
                        if uppercase:
                            string[i] = self.alphabet[letterpos - self.shift + len(self.alphabet)].upper()
                        else:
                            string[i] = self.alphabet[letterpos - self.shift + len(self.alphabet)]
                    else:
                        if uppercase:
                            string[i] = self.alphabet[letterpos - self.shift].upper()
                        else:
                            string[i] = self.alphabet[letterpos - self.shift]
                except:
                    string[i] = string[i]
                

            words[word] = "".join(string)

        return " ".join(words)
    
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
    import os
    cipher.update_lore()
    
    # current_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
    # lore_dir = os.path.abspath(os.path.join(current_dir, '..', 'story', 'lore_text', 'actual_lore.txt'))
    # with open(lore_dir, "r") as lore_file:
    #     lore_lines = lore_file.read().split("\n")
    # for line in lore_lines:
    #     if line != ":":
    #         print(cipher.encoder(line))
    #     else:
    #         print(":")
