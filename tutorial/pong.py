import sys
import sdl2
import sdl2.ext

from collections import namedtuple
from random import randint

BLUE = sdl2.ext.Color(0, 0, 255)
WHITE = sdl2.ext.Color(255, 255, 255)

EntitySet = namedtuple('EntitySet', ['ball', 'player1', 'player2'])
Rectangle = namedtuple('Rectangle', ['left', 'top', 'right', 'bottom'])

class SoftwareRenderer(sdl2.ext.SoftwareSpriteRenderSystem):

    def __init__(self, window, fence):
        super().__init__(window)
        self.fence = fence

    def _draw_net(self):
        minx, miny, maxx, maxy = self.fence
        x = minx + (maxx - minx) // 2
        for y in range(miny, maxy, 10):
            sdl2.ext.line(self.surface, WHITE, [x, y, x, y + 5], 1)

    def render(self, components):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        self._draw_net()
        super().render(components)

class CollisionSystem(sdl2.ext.Applicator):

    def __init__(self, fence):
        super().__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.entities = None
        self.fence = fence

    def _overlap(self, item):
        pos, sprite = item
        ball = self.entities.ball
        if sprite == ball.sprite:
            return False

        left, top, right, bottom = sprite.area
        bleft, btop, bright, bbottom = ball.sprite.area

        return (bleft < right and bright > left and
                btop < bottom and bbottom > top)

    def process(self, world, componentsets):
        ball, player1, player2 = self.entities
        minx, miny, maxx, maxy = self.fence
        collitems = [comp for comp in componentsets if self._overlap(comp)]
        if collitems:
            ball.velocity.vx = -ball.velocity.vx

            sprite = collitems[0][1]
            ballcentery = ball.sprite.y + ball.sprite.size[1] // 2
            halfheight = sprite.size[1] // 2
            stepsize = halfheight // 10
            degrees = 0.7
            paddlecentery = sprite.y + halfheight
            if ballcentery < paddlecentery:
                factor = (paddlecentery - ballcentery) // stepsize
                ball.velocity.vy = -int(round(factor * degrees))
            elif ballcentery > paddlecentery:
                factor = (ballcentery - paddlecentery) // stepsize
                ball.velocity.vy = int(round(factor * degrees))
            else:
                ball.velocity.vy = -ball.velocity.vy

        if (ball.sprite.y <= miny or
            ball.sprite.y + ball.sprite.size[1] >= maxy):
            ball.velocity.vy = -ball.velocity.vy

        if (ball.sprite.x <= minx or
            ball.sprite.x + ball.sprite.size[0] >= maxx):

            winner = player2 if ball.sprite.x <= minx else player1
            winner.playerdata.score += 1
            scores = (player1.playerdata.score, player2.playerdata.score)
            print("Score: {} to {}".format(*scores))

            bwidth = ball.sprite.size[0]
            bcenterx = minx + (maxx - minx) // 2
            ball.sprite.x = bcenterx - bwidth // 2

            bheight = ball.sprite.size[1]
            bcentery = miny + (maxy - miny) // 2
            ball.sprite.y = bcentery - bheight // 2

            ball.velocity.vx = -3
            ball.velocity.vy = randint(0, 6)

class MovementSystem(sdl2.ext.Applicator):

    def __init__(self, fence):
        super().__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.fence = fence

    def process(self, world, componentsets):
        minx, miny, maxx, maxy = self.fence
        for velocity, sprite in componentsets:
            swidth, sheight = sprite.size
            sprite.x += velocity.vx
            sprite.y += velocity.vy

            sprite.x = max(minx, sprite.x)
            sprite.y = max(miny, sprite.y)

            pmaxx = sprite.x + swidth
            pmaxy = sprite.y + sheight
            if pmaxx > maxx:
                sprite.x = maxx - swidth
            if pmaxy > maxy:
                sprite.y = maxy - sheight

class Velocity:

    def __init__(self):
        self.vx = 0
        self.vy = 0

class TrackingAIController(sdl2.ext.Applicator):

    def __init__(self, fence):
        super().__init__()
        self.componenttypes = PlayerData, Velocity, sdl2.ext.Sprite
        self.ball = None
        self.fence = fence

    def process(self, world, componentsets):
        for pdata, vel, sprite in componentsets:
            if not pdata.ai:
                continue

            centery = sprite.y + sprite.size[1] // 2
            if self.ball.velocity.vx < 0:
                # ball is moving away from the AI
                miny, maxy = self.fence.top, self.fence.bottom
                court_centery = miny + (maxy - miny) // 2
                if centery <  court_centery:
                    vel.vy = 3
                elif centery > court_centery:
                    vel.vy = -3
                else:
                    vel.vy = 0
            else:
                bcentery = self.ball.sprite.y + self.ball.sprite.size[1] // 2
                if bcentery < centery:
                    vel.vy = -3
                elif bcentery > centery:
                    vel.vy = 3
                else:
                    vel.vy = 0

class PlayerData:

    def __init__(self):
        self.ai = False
        self.score = 0

class Player(sdl2.ext.Entity):

    def __init__(self, world, sprite, posx=0, posy=0, ai=False):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()
        self.playerdata = PlayerData()
        self.playerdata.ai = ai

class Ball(sdl2.ext.Entity):

    def __init__(self, world, sprite, posx=0, posy=0):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()

def run():
    sdl2.ext.init()
    window = sdl2.ext.Window("The Pong Game", size=(800, 600))
    window.show()

    world = sdl2.ext.World()
    fence = Rectangle(0, 0, 800, 600)

    aicontroller = TrackingAIController(fence)
    movement = MovementSystem(fence)
    collision = CollisionSystem(fence)
    spriterenderer = SoftwareRenderer(window, fence)

    world.add_system(aicontroller)
    world.add_system(movement)
    world.add_system(collision)
    world.add_system(spriterenderer)

    factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
    sp_paddle1 = factory.from_color(WHITE, size=(20, 100))
    sp_paddle2 = factory.from_color(WHITE, size=(20, 100))
    sp_ball = factory.from_color(BLUE, size=(20, 20))

    player1 = Player(world, sp_paddle1, 0, 250)
    player2 = Player(world, sp_paddle2, 780, 250, True)

    ball = Ball(world, sp_ball, 390, 290)
    ball.velocity.vx = -3

    collision.entities = EntitySet(ball, player1, player2)
    aicontroller.ball = ball

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_UP:
                    player1.velocity.vy = -3
                elif event.key.keysym.sym == sdl2.SDLK_DOWN:
                    player1.velocity.vy = 3
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym in (sdl2.SDLK_UP, sdl2.SDLK_DOWN):
                    player1.velocity.vy = 0
        sdl2.SDL_Delay(10)
        world.process()

if __name__ == "__main__":
    run()
