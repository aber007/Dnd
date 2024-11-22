class cipher:
    alphabet = list("abcdefghijklmnopqrstuvwxyz")
    test = "When it’s almost his turn to go up on the gallows, a strange hooded figure appears and asks if he wants a second chance. He eagerly says yes, unknowingly signing a contract with the figure. When he gets hanged and the boards drop, everything goes black."
    testsimple = "aaabbb cccddd..."
    shift = 7

    def encoder(self, str):
        words = str.split()
        for word in range(len(words)):
            string = list(words[word])

            for i in range(len(string)):
                try:
                    try:
                        letterpos = self.alphabet.index(string[i])
                    except:
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
                except:
                    string[i] = string[i]
                
                uppercase = False

            words[word] = "".join(string)

        return " ".join(words)
    

    def decoder(self, str):
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
    
Cipher = cipher()

print(Cipher.encoder(Cipher.test))
