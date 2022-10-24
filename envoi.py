
# Installation des dépendances
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import clear_output
from scipy.io.wavfile import read,write
import sounddevice as sd
from scipy.signal import periodogram
import socket
import json

# PHASE D'EMISSION


#Message à envoyer à l'agence.
#Ici, la fonction input() renvoie une valeur dont le type correspond à ce que l'utilisateur a entré. 

#message_envoie = str(input("Veuillez entrer votre message (5 à 10 caractères) : "))
message_envoie = "salut"
#Vérification des conditions (tant que notre message n'est pas entre 5 et 10 caractères, nous restons dans la boucle).
while not 5 <= len(message_envoie) <= 10:
    clear_output()
    message_envoie = str(input("Veuillez entrer votre message (5 à 10 caractères) : "))


# CONVERSION DU MESSAGE EN ASCII PUIS EN BINAIRE


text_to_binary = "" #Variable dans laquelle sera notre texte converti en binaire.
for x in message_envoie:
    text_to_binary += bin(ord(x))[2:].zfill(8) #Ici, nous convertissons chaque caractères de notre mesage en binaire et les concaténons.

message = []
message[:] = text_to_binary #Ajoute chaque caractère du tableau un à un dans un tableau message.

message_int = text_to_binary
message_int = [0 if i=="0"else 1 for i in message] #Ici, nos éléments du tableau "message" était sous la forme de str, nous remplaçons donc ces valeurs par des entiers dans le tableau "message_int".
print(f"Conversion du message en binaire: {message_int}")


# BIT DE PARITE


#On initialise nos variables c et i étant égale à 0
#La variable c correspond à notre bit de parité (au niveau de l'émission)

c=0
i=0
bit_parite = 0
#Calcul du nombre de 1 dans notre message binaire, si le nombre est impair, notre bit de parité est
#à 1. Sinon 0.
for i in message_int:
    if i==1:
        c += 1
        if c%2 == 0:
            bit_parite = 1
        else:
            bit_parite = 0
    
print(f"Il y a {c} « 1 » dans notre message binaire.")  
print(f"Le bit de parité est donc à {bit_parite}.")


# CREATION DE LA TRAME


#On redéfinit c pour qu'il soit considéré comme un tableau pour pouvoir l'additionner avec d'autre tableau
bit_parite = [bit_parite]

#On définit la valeur de notre fanion de départ et de celui de fin
fanion1 = [0,1,1,1,1,1,1,0]
fanion2 = [0,1,1,1,1,1,1,0]

#On ajoute nos fanions ainsi que notre bit de parité au message binaire afin de former une trame
trame = fanion1 + message_int + bit_parite + fanion2

#On affiche notre trame
print(f"L'allure de la trame est la suivante : \n{trame}")


# CONTROLE DE REDONDANCE CYCLIQUE (EMETEUR)


trame_str = ""
for elem in trame:  
    trame_str += str(elem)

# Fonction XOR  utilisée par division 
def xor(a, b):
    # initialiser le résultat
    result = [] 
    # si les bits sont idem, alors XOR vaut 0, sinon 1
    for i in range(1, len(b)): 
        if a[i] == b[i]: 
            result.append('0') 
        else: 
            result.append('1') 
   
    return ''.join(result) 
   
# Division euclidienne
def div_eucli(divise, diviseur): 
   
    pick = len(diviseur) 
    tmp = divise[0 : pick] 
   
    while pick < len(divise): 
   
        if tmp[0] == '1': 

            tmp = xor(diviseur, tmp) + divise[pick] 
   
        else:    
            tmp = xor('0'*pick, tmp) + divise[pick] 
    
        pick += 1
    
    if tmp[0] == '1': 
        tmp = xor(diviseur, tmp) 
    else: 
        tmp = xor('0'*pick, tmp) 
   
    checkword = tmp 
    return checkword 
    

# Fonction d'encodage 
# On lui donne les données (augmentée de N-bits 0 qui est la taille de la clé) et la clé (Key) qui (polynome générateur)
def encodeData(data, key): 
    l_key = len(key) 

    appended_data = data + '0'*(l_key-1) 
    remainder = div_eucli(appended_data, key) 
   

    codeword = data + remainder 
    return codeword

key= '10011'
print(f"les données à envoyer sont : {trame_str}")
print (f"La clé CRC est : {key}")


data_crc = encodeData(trame_str, key)
# print("Encoded data for transmission: ", Encoded_data)
data_crc= [0 if i=="0"else 1 for i in data_crc]

print (f"les données encodées avec la clé key sont : {data_crc}")


# ENCODAGE MANCHESTER
# Pour coder le signal en Manchester (ici c'est une matrice binaire, provenant d'une conversion d'un texte en binaire), il faut faire une boucle avec un pas de 1. On commence par 0 et on fait 1 boucle pour chaque bit du message. Dans cette boucle on met une fonction if qui dit vérifie le bit de la matrice: si le bit est 0, alors on met un 0 puis un 1 dans notre nouvelle matrice, sinon (si le bit est 1) on met un 1 puis un 0.
# 
# On aura au final une matrice deux fois plus grande avec à chaque fois le bit de l'information et un bit de codage qui rend le tout illisible. On a donc codé notre information.


codeManchester = [] # Initialisation de la matrice

for i in range (0,len(data_crc)):  # Boucle qui va de 0 au nombre total de bits du message
    if data_crc[i]==0:             # Si le bit est 0
 
        codeManchester.append(0)  # Bit de l'information
        codeManchester.append(1)  # Bit de codage (sans réel sens)
 
    else:                         # Si le bit est 1
 
        codeManchester.append(1)  # Bit de l'information
        codeManchester.append(0)  # Bit de codage (sans réel sens)
        
print (f"\nLes données codées en Manchester donnent : {codeManchester}")


# MODULATION ASK

M = codeManchester # Message binaire M
Fe =  44100 # Fréquence d'échantillonnage
                         
baud = 300 # Débit souhaité sur le canal de transmission exprimé en bit/s
Nbits =  len(M) # Nombre de bits initial (taille du message M)
Ns = int(Fe/baud) # Nombre de symboles par bit (Fréq d'echan / Débit binaire) 
N = int(Ns*Nbits) # Nombre de bits total à moduler (Nombre de symboles par bit * Nombre de bits


# On génère le message binaire dupliqué
M_duplique= np.repeat(M,Ns) # On peut aussi le faire avec la fonction tile de numpy
                                     
# On génère le vecteur temps
t = np.linspace(0,N/Fe,N)   
print("----------T------------")                     
print(t)
print("------------")
# On génère la porteuse P(t)
Ap = 1                     
Fp =20000 # Fréquence de l'onde porteuse 
Porteuse = Ap*np.sin(2*np.pi*Fp*t)             

# On réalise la modualtion en amplitude  
ASK =  M_duplique*Porteuse   
M_envoie = np.array(len(M))
print('----------------------------------------------')
np.savetxt("donnees.csv", t, footer=f"{len(M)}")

# inputs = ["donnees.csv", "len.csv"] 

# # First determine the field names from the top line of each input file
# # Comment 1 below
# fieldnames = []
# for filename in inputs:
#   with open(filename, "r", newline="") as f_in:
#     reader = csv.reader(f_in)
#     headers = next(reader)
#     for h in headers:
#       if h not in fieldnames:
#         fieldnames.append(h)

# # Then copy the data
# with open("out.csv", "w", newline="") as f_out:   # Comment 2 below
#   writer = csv.DictWriter(f_out, fieldnames=fieldnames)
#   for filename in inputs:
#     with open(filename, "r", newline="") as f_in:
#       reader = csv.DictReader(f_in)  # Uses the field names in this file
#       for line in reader:
#         # Comment 3 below
#         writer.writerow(line)

# CONVERSION NUMERIQUE/ANALOGIQUE
write("message_son.wav",Fe,ASK)
_,analogue_message = read('message_son.wav')

sd.play(analogue_message, Fe)# L'instruction sd.play permet de jouer le son d'un fichier
status = sd.wait() # Attendre la fin du son

#Envoi du fichier audio
(HOST,PORT) = ('10.192.128.222',64000)
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.connect((HOST,PORT)) #Connexion au serveur sur l'IP et le port défini
with open('message_son.wav', 'rb') as f: #Ouverture du fichier
  for l in f: s.sendall(l) #envoi des donnees
s.close() #fermeture de la connexion

(HOST2,PORT2) = ('10.192.128.222',62000)
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.connect((HOST2,PORT2))
with open("donnees.csv", 'rb') as f:
  for l in f: s.sendall(l)
s.close()
