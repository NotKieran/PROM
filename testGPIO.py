import RPi.GPIO as GPIO
import time
PIN = 18
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while True:
        print GPIO.input(PIN)
	time.sleep(0.5)


gpio_setup()
