import serialBox, time, gameIO, sched, smbus, math, random
import RPi.GPIO as GPIO
import time

window_width = 80
window_height = 40


class Player(serialBox.line):
    def __init__(self, paddle_x, paddle_y, paddle_length, paddle_color, paddle_address, pin_serve, pin_size, ldr, adc_button, screen):
        serialBox.line.__init__(self, paddle_x, paddle_y, paddle_length, paddle_color, "vertical")
        self.serves = 5
        self.coordinates = []
        self.powerup = 2
        self.screen = screen
        self.draw(self.screen)
        self.adc_button = adc_button
        self.pin_serve = pin_serve
        self.pin_size = pin_size
        self.I2CADDR = 0x21
        self.paddle_address = paddle_address
        self.bus = smbus.SMBus(1)
        self.ldr = ldr

        bounce = 300
        if self.adc_button:
            GPIO.setup(self.pin_size, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            GPIO.setup(self.pin_serve, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.pin_size, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.pin_size, GPIO.RISING, callback=self.paddle_size_callback, bouncetime=bounce)

    def update(self):
        y = self.get_position
        if abs(y - self.y) > 0.5:
            self.move(y)

    def collision_update(self):
        self.draw(self.screen)


    def move(self, y):
        if window_height + 1  - (self.length - 1) > y > 0:
            if int(self.y != int(y)):
                self.clear(self.screen)
                self.y = y
                self.draw(self.screen)
            else:
                self.y = y
        elif y > window_height:
            y = window_height - (self.length - 1)
            if int(self.y != int(y)):
                self.clear(self.screen)
                self.y = y
                self.draw(self.screen)
        elif y < 1:
            y = 1
            if int(self.y != int(y)):
                self.clear(self.screen)
                self.y = y
                self.draw(self.screen)

    def serve_button(self):
        if self.adc_button:
            total = []
            for i in range(10):
                tmp = self.bus.read_word_data(self.I2CADDR, self.pin_serve)
                # Swap bytes round
                tmp1 = tmp << 8
                tmp2 = tmp >> 8
                tmp = tmp1 | tmp2
                # Remove high nibble (4 bits)
                tmp &= 4095
                total.append(tmp)
            tmp = max(set(total), key=total.count)

            if tmp < 200:
                return True
            else:
                return False
        else:
            if GPIO.input(self.pin_serve):
                return True
            else:
                return False

    @property
    def get_position(self):
        total = []
        if self.ldr:
            for i in range(80):
                tmp = self.bus.read_word_data(self.I2CADDR, self.paddle_address)
                # Swap bytes round
                tmp1 = tmp << 8
                tmp2 = tmp >> 8
                tmp = tmp1 | tmp2
                # Remove high nibble (4 bits)
                tmp = tmp & 4095
                total.append(41- int(tmp - 900)/62)

            print max(set(total), key=total.count)
            return max(set(total), key=total.count)
        else:
            for i in range(30):
                tmp = self.bus.read_word_data(self.I2CADDR, self.paddle_address)
                # Swap bytes round
                tmp1 = tmp << 8
                tmp2 = tmp >> 8
                tmp = tmp1 | tmp2
                # Remove high nibble (4 bits)
                tmp &= 4095
                total.append(int(tmp / 83))

            return max(set(total), key=total.count)

    def paddle_size_callback(self,channel):

        self.change_paddle_size(True)

    def change_paddle_size(self, bigger):
        if self.powerup > 0 and self.length == 3 and bigger:
            self.clear(self.screen)
            self.length = 6
            self.draw(self.screen)
            self.powerup -= 1
        else:
            self.clear(self.screen)
            self.length = 3
            self.draw(self.screen)



class Game:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.screen = serialBox.screen(window_width, window_height)
        self.screen.clear()
        self.winner = False
        # Initialise players
        self.players = {'player1': Player(3, 3, 3, serialBox.colors.RED, 0x10, 9, 17, False, False, self.screen),
                        'player2': Player(78, 3, 3, serialBox.colors.BLUE, 0x20, 0x40, 4, False, True, self.screen)}

        # Initialise scoreboard
        self.scorePlayer1 = 0
        self.scorePlayer2 = 0

        self.scoreboard = {'player1': Score(window_width / 2 - 11, 2, serialBox.colors.WHITE, self.screen,
                                            self.scorePlayer1),
                           'player2': Score(window_width / 2 + 8, 2, serialBox.colors.WHITE, self.screen,
                                            self.scorePlayer2)}

        self.scoreboard['player1'].draw()
        self.scoreboard['player2'].draw()

        # Initialise the ball
        ball_x = int((window_width / 2)+1)
        ball_y = int(window_height / 2)

        ball_radius = 1

        ball_color = serialBox.colors.GREEN

        self.ball = Ball(ball_x, ball_y, ball_radius, ball_color, 'regular', self.screen)

        # Initialise 

        self.net = Net(window_width / 2, 1, serialBox.colors.WHITE, self.screen)

        # Initialise the Paddles
        self.lights = {'L0':5,'L1':6,'L2':12,'L3':13,'L4':16,'L5':19,'L6':20,'L7':26}
        for pin in self.lights.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

    @property
    def round(self):
        return self.scoreboard['player1'].value + self.scoreboard['player2'].value

    def paddle_ball_collision(self):
        if self.ball.dir_x == 1 and self.players['player2'].y <= self.ball.y <= (
                    self.players['player2'].y + self.players['player2'].length) and self.ball.x >= (
        self.players['player2'].x -1):
            self.players['player2'].collision_update()
            self.players['player2'].change_paddle_size(False)
            if self.ball.y == self.players['player2'].y or self.ball.y == self.players['player2'].y + self.players['player2'].length:
                self.ball.speedY = self.ball.speedX * 3
            else:
                self.ball.speedY = self.ball.speedX/2
            return True
        elif self.ball.dir_x == -1 and self.players['player1'].y <= self.ball.y <= (
                    self.players['player1'].y + self.players['player1'].length) and self.ball.x <= (
                    self.players['player1'].x +2):
            self.players['player1'].change_paddle_size(False)
            if self.ball.y == self.players['player1'].y or self.ball.y == self.players['player1'].y + self.players[
                'player1'].length:
                self.ball.speedY = self.ball.speedX * 3
            else:
                self.ball.speedY = self.ball.speedX/2
            self.players['player1'].collision_update()
            return True
        else:
            return False


    def exit(self):
        print "exiting"
        GPIO.remove_event_detect(self.players['player1'].pin_size)
        GPIO.remove_event_detect(self.players['player2'].pin_size)
        GPIO.cleanup()

        del self.screen
        del self.ball
        del self.players


    def update(self):
        blocked_coordinates = (
            self.scoreboard['player1'].coordinates + self.scoreboard['player2'].coordinates + self.net.coordinates)
        self.ball.update(blocked_coordinates)
        self.players['player1'].update()
        self.players['player2'].update()
        self.update_scoreboard()
        self.update_ball_light()
        if self.paddle_ball_collision():
            self.ball.random_speedX()
            self.ball.bounce('x')

    def update_ball_light(self):
        GPIO.setmode(GPIO.BCM)
        light = math.ceil(self.ball.x / 10)
        if light == 1:
            for pin in self.lights.values():
                GPIO.output(pin,0)
            GPIO.output(self.lights['L0'], 1)

        elif light == 2:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L1'], 1)

        elif light == 3:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L2'], 1)

        elif light == 4:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L3'], 1)

        elif light == 5:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L4'], 1)

        elif light == 6:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L5'], 1)

        elif light == 7:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L6'], 1)

        elif light == 8:
            for pin in self.lights.values():
                GPIO.output(pin, 0)
            GPIO.output(self.lights['L7'], 1)

    def update_scoreboard(self):
        if self.ball.hit_left():

            self.player2_scores()

        elif self.ball.hit_right():

            self.player1_scores()

    def player1_scores(self):
        self.scorePlayer1 += 1
        gameIO.point_scored()

        if self.players['player1'].serves >= 1:
            self.players['player1'].serves -= 1
            self.scoreboard['player1'].update_score(self.scorePlayer1)
            self.serve(1)
        elif self.players['player2'].serves >= 1:
            self.players['player2'].serves -= 1
            self.scoreboard['player1'].update_score(self.scorePlayer1)
            self.serve(2)
        elif self.players['player1'].serves == 0 and self.players['player2'].serves == 0:
            if self.scorePlayer2 != 10 and self.scorePlayer1 !=10:
                self.scoreboard['player2'].update_score(self.scorePlayer2)            
                self.scoreboard['player1'].update_score(self.scorePlayer1)            
            self.pick_winner()

    def pick_winner(self):
        self.ball.dir_y = 0
        self.ball.dir_x = 0l
        self.ball.clear(self.screen)
        if self.scorePlayer1 >self.scorePlayer2:
            self.scoreboard['player1'].color = serialBox.colors.GREEN
            self.scoreboard['player2'].color = serialBox.colors.DEFAULTBACKGROUND
            self.scoreboard['player1'].clear()
            self.scoreboard['player2'].clear()
            self.scoreboard['player1'].draw()
            self.scoreboard['player2'].draw()
            time.sleep(5)
            self.winner = True
        elif self.scorePlayer2 >  self.scorePlayer1:
            self.scoreboard['player2'].color = serialBox.colors.GREEN
            self.scoreboard['player1'].color = serialBox.colors.DEFAULTBACKGROUND
            self.scoreboard['player1'].clear()
            self.scoreboard['player2'].clear()
            self.scoreboard['player1'].draw()
            self.scoreboard['player2'].draw()
            time.sleep(5)
            self.winner = True
        elif self.scorePlayer1 == self.scorePlayer2:
            self.scoreboard['player2'].color = serialBox.colors.GREEN
            self.scoreboard['player1'].color = serialBox.colors.GREEN
            self.scoreboard['player1'].clear()
            self.scoreboard['player2'].clear()
            self.scoreboard['player1'].draw()
            self.scoreboard['player2'].draw()
            time.sleep(5)
            self.winner = True

    def player2_scores(self):
        self.scorePlayer2 += 1
        gameIO.point_scored()
        if self.players['player1'].serves >= 1:
            self.players['player1'].serves -= 1
            self.scoreboard['player2'].update_score(self.scorePlayer2)
            self.serve(1)
        elif self.players['player2'].serves >= 1:
            self.players['player2'].serves -= 1
            self.scoreboard['player2'].update_score(self.scorePlayer2)
            self.serve(2)
        elif self.players['player1'].serves == 0 and self.players['player2'].serves == 0:
            if self.scorePlayer2 != 10 and self.scorePlayer1 !=10:
                self.scoreboard['player2'].update_score(self.scorePlayer2)            
                self.scoreboard['player1'].update_score(self.scorePlayer1)            
            self.pick_winner()

    def serve(self, player):
        ball_speed = self.ball.speedX
        self.ball.speedX = 0
        self.screen.clear()
        self.net.draw(self.screen)
        self.scoreboard['player1'].draw()
        self.scoreboard['player2'].draw()
        self.players['player1'].draw(self.screen)
        self.players['player2'].draw(self.screen)


        print "serve"
        if player == 1:
            while self.players['player1'].serve_button() == False:
                self.players['player1'].update()
                self.players['player2'].update()
                new_ball_x = self.players['player1'].x + 1
                new_ball_y = self.players['player1'].y + 1
                self.ball.dir_x = 1
                self.ball.move(new_ball_x, new_ball_y)

        elif player == 2:
            while self.players['player2'].serve_button() == False:
                self.players['player1'].update()
                self.players['player2'].update()
                new_ball_x = self.players['player2'].x - 1
                new_ball_y = self.players['player2'].y + 1
                self.ball.dir_x = -1
                self.ball.move(new_ball_x, new_ball_y)
        self.ball.speedX = ball_speed


class Ball(serialBox.rect):
    """docstring for Ball"""

    def __init__(self, x, y, radius, color, speed, screen):
        super(Ball, self).__init__(x, y, radius, radius, color)
        self.set_speedX(speed)
        self.dir_x = -1
        self.dir_y = -1
        self.speedY = self.speedX/2
        self.screen = screen
        self.draw(self.screen)

    def random_speedX(self):
        speeds = ["slow", "regular", "fast"]
        self.set_speedX(speeds[random.randint(0, 2)])

    def set_speedX(self, speed):
        if speed == "slow":
            self.speedX = 0.40
        elif speed == "regular":
            self.speedX = 0.55
        elif speed == "fast":
            self.speedX = 0.70
        else:
            raise ValueError("Bad value for ball speed, please pass 'slow', 'regular' or 'fast'")

    def move(self, new_x, new_y):
        if int(new_x) != int(self.x) or int(new_y) != int(self.y):
            self.clear(self.screen)
            self.x = new_x
            self.y = new_y
            self.draw(self.screen)

    def update(self, blockedCordinates):
        new_x = self.x + (self.dir_x * self.speedX)
        new_y = self.y + (self.dir_y * self.speedY)
        if int(new_x) != int(self.x) or int(new_y) != int(self.y):
            if not [int(self.x), int(self.y)] in blockedCordinates:
                self.clear(self.screen)
            self.x = new_x
            self.y = new_y

            if not [int(self.x), int(self.y)] in blockedCordinates:
                self.draw(self.screen)
        else:
            self.x = new_x
            self.y = new_y

        if self.hit_ceiling() or self.hit_floor():
            self.bounce('y')
        if self.hit_left() or self.hit_right():
            self.bounce('x')

    def bounce(self, axis):
        if axis == 'x':
            self.dir_x *= -1
        elif axis == 'y':
            self.dir_y *= -1

    def hit_ceiling(self):
        if self.dir_y == -1 and int(self.y) == 0:
            return True
        else:
            return False

    def hit_floor(self):
        if self.dir_y == 1 and self.y >= self.screen.height + 1:
            return True
        else:
            return False

    def hit_left(self):
        if self.x <= 1:
            return True
        else:
            return False
            # <size button code>

    def hit_right(self):
        if self.x >= self.screen.width:
            return True
        else:
            return False


class Score(serialBox.text):
    def __init__(self, x, y, color, screen, value):
        super(Score, self).__init__(x, y, color, screen, value)

    def update_score(self, new_score):
        if self.value != new_score:
            self.clear()
            self.value = new_score
            self.draw()


class Net(serialBox.line):
    def __init__(self, x, y, color, screen):
        serialBox.line.__init__(self, x, y, 0, color, 'vertical')
        self.screen = screen
        self.pattern = [[0, 2], [0, 3], [0, 6], [0, 7], [0, 10], [0, 11], [0, 14], [0, 15], [0, 18], [0, 19], [0,22], [0,23], [0,26], [0,27], [0,30], [0,31], [0,34], [0,35], [0,38], [0,39]]
        self.coordinates = []
        self.draw(self.screen)

    def draw(self, screen):
        output = ''
        self.coordinates = []
        for co in self.pattern:
            x = self.x + co[0]
            y = self.y + co[1]
            self.coordinates.append([x, y])
            output += self.formatPointToString(x, y, self.color)
        screen.output(output)
