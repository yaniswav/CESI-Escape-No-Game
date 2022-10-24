import matplotlib.pyplot as plt
import numpy as np
from IPython.display import clear_output
from scipy.io.wavfile import read,write
import sounddevice as sd
from scipy.signal import periodogram
import socket
import csv

# PHASE DE RECEPTION

(HOST,PORT) = ('10.192.128.222',64000) #Définition de l'addresse IP et du port sur lequel le serveur va écouter
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Création d'un socket (INET - STREAMING)
s.bind((HOST, PORT)) #Assigne l'adresse IP et le port à l'instance créée
print("Attente du message agent")
s.listen(1) #Rend le socket prêt à accepter une connexion
conn, addr = s.accept() #Accepte les connexions TCP d'un client

with open('message_son.wav','wb') as f:
  while True:
    l = conn.recv(1024) #Retourne les données reçues en bits avec comme le nombre de bits à recevoir comme paramètre
    if not l: break
    f.write(l) #écrit les données dans un fichier wav
s.close()


#Meme méthode que précédemment, ici, nous prenons les valeurs : la taille de notre message et t, le vecteur temps
(HOST2,PORT2) = ('10.192.128.222',62000)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST2, PORT2))
s.listen(1)
conn, addr = s.accept()
with open('donnees.csv','wb') as f:
  while True:
    l = conn.recv(1024)
    if not l: break
    f.write(l)
s.close()

#Lecture des données et mise en place dans un array
data=list()
fich = open(r'donnees.csv','r')
readfich = csv.reader(fich)
for j, row in enumerate(readfich):
  data.append(row)

fich.close()
a = np.asarray(data)
b = a[:-1]
liste = b.astype(np.float)
t = [liste[i][0] for i in range(len(liste))]
t = np.array(t)

# CONVERSION ANALOGIQUE/NUMERIQUE

f,ecoute_message = read('message_son.wav')


# FILTRAGE DU SIGNAL RECU PAR UN FILTRE PASSE-BANDE

M = a[-1]
M = "".join(M)
M = M.replace("# ", "")
M = int(M)

Fe =  44100 # Fréquence d'échantillonnage

baud = 300 # Débit souhaité sur le canal de transmission exprimé en bit/s
Nbits =  M # Nombre de bits initial (taille du message M)
Ns = int(Fe/baud) # Nombre de symboles par bit (Fréq d'echan / Débit binaire) 
N = int(Ns*Nbits) # Nombre de bits total à moduler (Nombre de symboles par bit * Nombre de bits

f2 = 3000                             # fréquence du signal S2
S2 = np.sin(2*np.pi*f2*t)            # création d'une sinusoïde de fréquence f2
Multi = ecoute_message*S2

Fe2 = 44100
f,FFT = periodogram(Multi,Fe2)

fc = 19000
FFT_filtre = FFT

for i in range(len(f)):
    if f[i] < fc: # on coupe toutes les fréquences < 19 000 Hz 
        FFT_filtre[i] = 0.0

# on calcule la transfomrée de Fourier inverse du signal après filtrage en utilsant la fonction ifft de Python
# la FFT inverse permet de revenir dans l'espace temporal (espace fréquentiel -> espace temps)
FFT_inverse = np.fft.ifft(FFT_filtre)
T = np.real(FFT_inverse) #Passage de la partie imaginaire vers la partie réelle

# # DEMODULATION ASK
Fp = 20000
Ap = 1
Porteuse = Ap*np.sin(2*np.pi*Fp*t)

S = Porteuse #générer la porteuse déja utilisée plus haut lors de la modulation (nommée Porteuse)

Produit = ecoute_message*S# multiplier le signal modulé par la signal de la porteuse S1 (bit 1)

# Intégration des 2 résultats bit1 et bit0 sur période de T = [0, Ns], Ns : taille du symbole envoyé 
# par la méthode des trapèzes (fonction numpy.trapz en Python) (l'approche la plus simple)  

recu = [] # Résulat de l'intégration                         

i = 0
for i in range(0,N,Ns):
    recu.append(np.trapz(Produit[i:i+Ns]))

# Remarque sur la fonction trapz :

  # on se contente d’intégrer sur un seul axe et c'est suffisant ici
  # si les données ne sont pas réparties uniformément par l'échantillonnage, il faut aussi intégrer sur l'axe des abscisses comme suit :
  # np.trapz(Produit[i:i+Ns],t[i:i+Ns]))


message_demodule_ASK = []

#Permet de transformer nos valeurs numériques en suite de 0 et de 1.
#Si la valeur est supérieure strictement à 0, on ajoute 1 à notre liste. Sinon 0.
for ii in range (0,len(recu)):
    if recu[ii] > 0:
        message_demodule_ASK.extend([int(1)]) 
    if recu[ii] <= 0:
        message_demodule_ASK.extend([int(0)])
print(message_demodule_ASK)


# # DECODAGE MANCHESTER
# Une fois l'information codée reçue, on doit la décoder. Comme c'est un codage Manchester, on doit retirer de la matrice les bits de codage. Comme on sait qu'on a mis d'abord le bit de l'information puis le bit de codage on doit faire une boucle qui a un pas de 2, le bit indiqué par cette boucle sera à chaque fois intégré dans une variable tableau, ce qui éliminera 1 bit sur 2, les bits de codage.

# message_decode = "".join(["0" if i==0 else "1" for i in message_demodule_ASK])
# print(message_decode)
            
message_decode = [int(message_demodule_ASK[i]) for i in range(0, len(message_demodule_ASK),2)]
print("La trame décodée par le codage manchester est la suivante:",message_decode)

# # CONTROLE DE REDONDANCE CYCLIQUE (RECEPTEUR)

bin_data1 = ""
for elem in message_decode:  
    bin_data1 += str(elem)

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
def mod2div(divident, divisor): 
   
    pick = len(divisor) 
    tmp = divident[0 : pick] 
   
    while pick < len(divident): 
   
        if tmp[0] == '1': 

            tmp = xor(divisor, tmp) + divident[pick] 
   
        else:    
            tmp = xor('0'*pick, tmp) + divident[pick] 
    
        pick += 1
    
    if tmp[0] == '1': 
        tmp = xor(divisor, tmp) 
    else: 
        tmp = xor('0'*pick, tmp) 
   
    checkword = tmp 
    return checkword 

 
# On donne la focntion décodeData les données encodées en CRC et la clé utilisée
def decodeData(data_crc, key): 
   
    l_key = len(key) 
    appended_data = data_crc + '0'*(l_key-1) 
    remainder = mod2div(appended_data, key) 
   
    return remainder 



key= '10011'   # On utilise la même clé à l'émission (polynome générateur)
check = decodeData(bin_data1, key) 



print("Le reste de la division après décodage est ->"+check) 
temp = "0" * (len(key) - 1) 


if check == temp: 
    print("Bravo! les données -> "+ bin_data1+ " <- sont bien reçues!") 
else: 
    print ("Erreur de réception !") 


# # RECUPERATION DU MESSAGE ISSU DE LA TRAME DE LA TRAME

#On supprime nos fanions afin de garder seulement notre message encode avec le controle de redondance cyclique
del message_decode[(len(message_decode)-12):(len(message_decode))]
del message_decode[0:8]

#On affiche la trame sans les fanions de début et de fin

message_crc= "".join(["0" if i==0 else "1" for i in message_decode])
print("Voici la trame sans les fanions de début et de fin",message_crc)

# # VERIFICATION DU BIT DE PARITE

#On calcul le bit de parité lors de la récéption du signal
c1=0
i=0

c0=message_decode[len(message_decode)-1]

#On supprime le dernier bit de la trame (elle correspond au bit de parité)
del message_decode[-1]

#On calcul le bit de parité
for i in range(len(message_decode)):
    if message_decode[i]==1:
        c1=c1+1 
    else:
        c1=c1
# if c1 == c:
#     print("Il n'y a pas d'erreur")
# else :
#     print("pas d'erreur")
#Affiche l'information du message texte en binaire
print(message_decode)

# # CONVERSION DU MESSAGE BINAIRE EN CHAINE DE CARACTERE

bin_data = ""
for elem in message_decode:  
    bin_data += str(elem)
    
data_reçu =' '

# Fonction BinarytoDecimal() function (conversion bianire ==> décimal)
def BinaryToDecimal(binary):  
    binary1 = binary 
    decimal, i, n = 0, 0, 0 #initialisation des variables
    
    while(binary != 0): 
        dec = binary % 10
        decimal = decimal + dec * pow(2, i) 
        binary = binary//10
        i += 1
    return (decimal)


# Découper les données binaire d'entrée et la convertir en décimal puis la convertir en chaîne par bloc de 8 
for i in range(0, len(bin_data), 8): 
    # découper le bin_data de la plage d'index [0, 7] (car une caractère ASCII est codé sur 7 bits) ett le stocker sous forme d'entier dans temp_data
    temp_data = int(bin_data[i+1:i+8])
      
       
    # Passer (temp_data) dans la fonction BinarytoDecimal ()
    # pour obtenir la valeur décimale correspondante de (temp_data)
    decimal_data = BinaryToDecimal(temp_data)

    # Décodage de la valeur décimale renvoyée par
    # la Fonction BinarytoDecimal (), en utilisant chr ()
    # fonction qui renvoie la chaîne correspondante
    # caractère pour une valeur ASCII donnée et enregistrez-le
    # dans data_recu
    data_reçu = data_reçu + chr(decimal_data) 

# Affichage du resultat 
print(f"Le message reçu est : {data_reçu}") 
