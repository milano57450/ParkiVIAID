# Import des modules nécessaires
from machine import Pin, time_pulse_us  # gestion des broches + mesure du temps
import time                             # gestion des délais

# -----------------------------
# CONFIGURATION DES CAPTEURS
# -----------------------------

# Capteur 1
trig1 = Pin(3, Pin.OUT)   # broche TRIG du capteur 1 (sortie)
echo1 = Pin(2, Pin.IN)    # broche ECHO du capteur 1 (entrée)

# Capteur 2
trig2 = Pin(5, Pin.OUT)   # broche TRIG du capteur 2 (sortie)
echo2 = Pin(4, Pin.IN)    # broche ECHO du capteur 2 (entrée)

# -----------------------------
# FONCTION DE MESURE DE DISTANCE
# -----------------------------

def distance(trig, echo):
    """
    Cette fonction mesure la distance à partir d’un capteur HC-SR04.
    Elle fonctionne avec n’importe quel couple (TRIG, ECHO).
    """

    # 1. On s'assure que TRIG est à 0 (état stable)
    trig.low()
    time.sleep_us(2)  # petite pause de stabilisation

    # 2. On envoie une impulsion de 10 µs pour déclencher le capteur
    trig.high()
    time.sleep_us(10)
    trig.low()

    # 3. On mesure la durée pendant laquelle ECHO reste à 1
    #    → correspond au temps aller-retour de l’onde ultrason
    duration = time_pulse_us(echo, 1, 30000)  # timeout 30 ms

    # 4. Si aucun signal reçu → erreur
    if duration < 0:
        return None

    # 5. Calcul de la distance :
    #    vitesse du son = 0.0343 cm/µs
    #    division par 2 car aller-retour
    d = (duration * 0.0343) / 2 

    return d  # distance en cm

# -----------------------------
# BOUCLE PRINCIPALE
# -----------------------------

while True:

    # ---- MESURE CAPTEUR 1 ----
    d1 = distance(trig1, echo1)  # mesure distance capteur 1
    time.sleep(0.1)  # pause pour éviter interférences entre capteurs

    # ---- MESURE CAPTEUR 2 ----
    d2 = distance(trig2, echo2)  # mesure distance capteur 2

    # -----------------------------
    # ÉTAT DES PLACES (seuil 50 cm)
    # -----------------------------

    # Place 1
    if d1 is None:
        print("Place 1 : Erreur capteur")
        place1 = False
    elif d1 <= 50:
        print("Place 1 : Occupée")
        place1 = True
    else:
        print("Place 1 : Libre")
        place1 = False

    # Place 2
    if d2 is None:
        print("Place 2 : Erreur capteur")
        place2 = False
    elif d2 <= 50:
        print("Place 2 : Occupée")
        place2 = True
    else:
        print("Place 2 : Libre")
        place2 = False

    # -----------------------------
    # ÉTAT GLOBAL
    # -----------------------------

    if place1 and place2:
        print("Les 2 places sont OCCUPÉES")
    elif not place1 and not place2:
        print("Les 2 places sont LIBRES")
    else:
        print("Une seule place est occupée")

    # -----------------------------
    # AFFICHAGE DES DISTANCES (DEBUG)
    # -----------------------------
    print("Distances : Capteur 1 =", d1, "cm | Capteur 2 =", d2, "cm")
    print("----------------------")

    # -----------------------------
    # PAUSE ENTRE CHAQUE MESURE
    # -----------------------------
    time.sleep(1)  # évite de spammer le terminal