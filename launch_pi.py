import serialBox, time, math, gameIO
from Game import *



import time


def create_game():
    gameIO.gpio_setup()
    GPIO.setup(18, GPIO.OUT)
    gameIO.play_mario()
    GPIO.cleanup()
    game = Game()
    game.players['player1'].serves -= 1
    game.serve(1)
    while not game.winner:
        game.update()
    game.exit()
    del game






create_game()
create_game()





print "\033[0m"
