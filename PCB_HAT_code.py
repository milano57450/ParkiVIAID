import RPi.GPIO as GPIO
import time

# Configuration
RED, GREEN, BLUE = 17, 27, 22
GPIO.setmode(GPIO.BCM)
GPIO.setup([RED, GREEN, BLUE], GPIO.OUT)

def signal_erreur():
    # Fait clignoter la LED bleue en cas de problème
    for _ in range(5):
        GPIO.output(BLUE, True)
        time.sleep(0.2)
        GPIO.output(BLUE, False)
        time.sleep(0.2)

# Test : Allumer Vert (Parking OK)
GPIO.output(GREEN, True)
time.sleep(2)

# Simulation erreur
GPIO.output(GREEN, False)
signal_erreur()

GPIO.cleanup()