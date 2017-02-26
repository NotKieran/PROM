import RPi.GPIO as GPIO
from PyGlow import PyGlow
from time import *

#####
#
# GPIO Configuration
#
#####

software_sound_pin = 18
hardware_sound_pin1 = 10
hardware_sound_pin2 = 11
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(hardware_sound_pin1, GPIO.OUT)
    GPIO.setup(hardware_sound_pin2, GPIO.OUT)

#####
#
# Module to play music
#
#####

def music_player(frequency, duration):
  duration = duration/1.5
  if(frequency==0):
    sleep(duration)
    return
  period = 1.0 / frequency
  half_period = period / 2
  cycles = int(duration * frequency)

  for i in range(cycles):
    GPIO.output(software_sound_pin, 1)
    sleep(half_period)
    GPIO.output(software_sound_pin, 0)
    sleep(half_period)


#####
#
# Module to send mario to music_player
#
#####

def play_mario():

  # Music from http://wiki.mikrotik.com/wiki/Super_Mario_Theme

  mario=[[660, 100], [0, 150], [660, 100], [0, 300], [660, 100], [0, 300], [510, 100], [0, 100], [660, 100], [0, 300], [770, 100], [0, 550], [380, 100], [0, 575], [510, 100], [0, 450], [380, 100], [0, 400],
                      [320, 100], [0, 500], [440, 100], [0, 300], [480, 80], [0, 330], [450, 100], [0, 150], [430, 100], [0, 300], [380, 100], [0, 200], [660, 80], [0, 200], [760, 50], [0, 150], [860, 100], [0, 300],
                      [700, 80], [0, 150], [760, 50], [0, 350], [660, 80], [0, 300], [520, 80], [0, 150], [580, 80], [0, 150], [480, 80], [0, 500], [510, 100], [0, 450], [380, 100], [0, 400], [320, 100], [0, 500],
                      [440, 100], [0, 300], [480, 80], [0, 330], [450, 100], [0, 150], [430, 100], [0, 300], [380, 100], [0, 200], [660, 80], [0, 200], [760, 50], [0, 150], [860, 100], [0, 300], [700, 80], [0, 150],
                      [760, 50], [0, 350], [660, 80], [0, 300], [520, 80], [0, 150], [580, 80], [0, 150], [480, 80]]


  for i in range(len(mario)):
    music_player(mario[i][0], mario[i][1]/1000.0)

#####
#
# Module to send beep to music_player
#
#####

def play_twobeep():
    try:
        GPIO.output(hardware_sound_pin1, 1)
        sleep(0.2)
        GPIO.output(hardware_sound_pin1, 0)
        sleep(0.1)
        GPIO.output(hardware_sound_pin2, 1)
        sleep(0.2)
        GPIO.output(hardware_sound_pin2, 0)
    except RuntimeError:
        gpio_setup()
        play_twobeep()

#####
#
# Module to control PyGlow
#
#####

def pyglow_flash():

    pyglow = PyGlow()
    val = 200
    glowtime=0.1

    pyglow.color('white',val)
    sleep(glowtime)
    pyglow.color('blue',val)
    sleep(glowtime)
    pyglow.color('green',val)
    sleep(glowtime)
    pyglow.color('yellow',val)
    sleep(glowtime)
    pyglow.color('orange',val)
    sleep(glowtime)
    pyglow.color('red',val)
    sleep(glowtime)
    pyglow.color('white',0)
    pyglow.color('blue',0)
    pyglow.color('green',0)
    pyglow.color('yellow',0)
    pyglow.color('orange',0)
    pyglow.color('red',0)


#####
#
# Module for when a point is scored
#
#####

def point_scored():
  play_twobeep()
  pyglow_flash()
