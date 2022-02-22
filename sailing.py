import pygame
import time
import random
import math
import os

resolution = (1600, 900)

def dist(self, other):
    return math.sqrt((self.x-other.x)**2+(self.y-other.y)**2)

def angleDiff(a,b):
    return math.pi - abs(abs(a - b) - math.pi);

def loadImage(name, r):
    image = pygame.image.load(os.path.join("textures", name))
    image = pygame.transform.scale(image, (r*2, r*2))
    return image

def blitRotate(surf,image, pos, originPos, angle):

    #ifx rad ddeg
    angle = -angle*180/math.pi

    # calcaulate the axis aligned bounding box of the rotated image
    w, h       = image.get_size()
    box        = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]
    min_box    = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box    = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

    # calculate the translation of the pivot 
    pivot        = pygame.math.Vector2(originPos[0], -originPos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move   = pivot_rotate - pivot

    # calculate the upper left origin of the rotated image
    origin = (int(pos[0] - originPos[0] + min_box[0] - pivot_move[0]), int(pos[1] - originPos[1] - max_box[1] + pivot_move[1]))

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle+180)
    surf.blit(rotated_image, origin)

class Game():

    def __init__(self):
        self.wind = Wind()
        self.players = [
        Player(controls = {"left":pygame.K_a,"right":pygame.K_d,"out":pygame.K_w,"in":pygame.K_s,"fire":pygame.K_SPACE}),
        #Player(controls = {"left":pygame.K_LEFT,"right":pygame.K_RIGHT,"out":pygame.K_UP,"in":pygame.K_DOWN,"fire":pygame.K_p})
        ]
        self.enemies = [Enemy()]

    def update(self):
        gameDisplay.fill((100,120,200))
        pressed = pygame.key.get_pressed()
        self.wind.update()
        self.wind.draw()
        for enemy in self.enemies:
            enemy.inputs(pressed)
            enemy.move()
            enemy.draw()
        self.enemies = [ship for ship in self.enemies if ship.hp>0]
        for player in self.players:
            player.inputs(pressed)
            player.move()
            player.draw()
            print(player.hp)
        self.players = [ship for ship in self.players if ship.hp>0]

class Wind():

    def __init__(self):
        self.angle = 1
        self.strength = 1.5
        self.x = 100
        self.y = 100

    def update(self):
        #self.strength*=0.9999
        #self.strength*=1.00001 #for extremely little quote difference
        self.strength+=(random.random()-0.5)*0.01
        if self.strength<0:
            self.strength+=0.01 #or just abs it idk
        self.angle+=(random.random()-0.5)*0.02/self.strength
        self.angle = self.angle%math.tau

    def draw(self):
        sin = math.sin(self.angle)
        cos = math.cos(self.angle)
        pygame.draw.line(gameDisplay, (0,0,0), (int(self.x),int(self.y)),(int(self.x+cos*self.strength*100),int(self.y+sin*self.strength*100)),10)

class Cannonball():

    def __init__(self, owner, x, y, angle):
        self.owner = owner
        self.x = x
        self.y = y
        self.xv = math.cos(angle)*5 + math.cos(owner.angle)*owner.speed
        self.yv = math.sin(angle)*5 + math.sin(owner.angle)*owner.speed
        self.age = 0

    def move(self): 
        self.age+=1
        self.x+=self.xv
        self.y+=self.yv
        for ship in game.players+game.enemies:
            if ship == self.owner:
                continue
            if dist(self, ship)<20:
                ship.hurt()

    def draw(self):
        pygame.draw.ellipse(gameDisplay, (50,50,50), (int(self.x),int(self.y),10,10), 0)

class Ship():
    image = loadImage("ship.png",50)
    sinkingImage = loadImage("ship_sinking.png",50)

    def __init__(self):
        self.hp = 1
        self.angle= -1 #inte 0 lol. pngn blir weird
        self.sailAngle=0
        self.radius = 50
        self.speed = 0
        self.mainsheetAngle = math.pi
        self.projectiles = []
        self.cooldown = 0
        self.burning = 0
        self.brokenMast = 0

    def move(self):
        if self.burning:
            self.hp-=0.001

        self.cooldown = max(self.cooldown-1, 0)

        #fix angles
        self.angle=self.angle%math.tau
        self.mainsheetAngle = max(0.1,min(1,self.mainsheetAngle))

        #calculate relative wind
        wx = math.cos(game.wind.angle)*game.wind.strength
        wy = math.sin(game.wind.angle)*game.wind.strength
        wx -= math.cos(self.angle)*self.speed
        wy -= math.sin(self.angle)*self.speed
        wa = math.atan2(wy,wx)
        wv = math.sqrt(wx**2 + wy**2)

        print(self.speed, game.wind.strength, wv)


        if not self.brokenMast:
            #calculate sailAngle
            if angleDiff(-wa+self.angle, 0)<self.mainsheetAngle:
                self.sailAngle = wa
            else:
                if angleDiff(self.sailAngle,wa+math.pi/2)<math.pi/2:
                    self.sailAngle = -self.mainsheetAngle+self.angle
                else:# angleDiff(self.sailAngle,wind.angle+math.pi)>math.pi:
                    self.sailAngle = self.mainsheetAngle+self.angle
                self.sailAngle = self.sailAngle%math.tau

            #calculate boat acceleration
            a = math.sin(self.sailAngle-wa) * math.sin(self.angle-self.sailAngle) * wv * 0.01
            self.speed-=a #-? w

        #move
        self.x+=math.cos(self.angle)*self.speed #simple multiplier for game speed
        self.y+=math.sin(self.angle)*self.speed      
        self.speed*=0.998
        #drag
        self.x+=math.cos(game.wind.angle)*game.wind.strength*0.1
        self.y+=math.sin(game.wind.angle)*game.wind.strength*0.1
        #screenwrapping
        if self.x>resolution[0]+50:
            self.x=-30
        if self.x<-50:
            self.x=resolution[0]+30
        if self.y>resolution[1]+50:
            self.y=-30
        if self.y<-50:
            self.y=resolution[1]+30

        #collide
        for ship in game.players+game.enemies:
            if ship == self:
                continue
            if dist(self, ship)<50:
                ship.hurt(abs(self.speed*0.2))
                self.hurt(abs(ship.speed*0.2))
                ship.speed*=0.5
                self.speed*=0.5

        #cannonballs
        for proj in self.projectiles:
            proj.move()
        self.projectiles = [proj for proj in self.projectiles if proj.age<30]

    def shoot(self):
        rightAngle = (self.angle + math.pi/2)%math.tau
        leftAngle = (self.angle - math.pi/2)%math.tau
        for i in [-1,0,1]:
            xOffset = math.cos(self.angle)*i*5
            yOffset = math.sin(self.angle)*i*5
            self.projectiles.append(Cannonball(self, self.x+xOffset, self.y+yOffset, rightAngle-i*0.2))
            self.projectiles.append(Cannonball(self, self.x+xOffset, self.y+yOffset, leftAngle+i*0.2))

    def hurt(self, damage=0.1): #every frame of contact with cannonball
        self.hp-=damage
        if random.random()<damage:
            self.burning = 1
        if random.random()<damage:
            self.brokenMast = 1

    def draw(self):
        for proj in self.projectiles:
            proj.draw()
        
        sin = math.sin(self.angle)
        cos = math.cos(self.angle)
        sailCos = math.cos(self.sailAngle)
        sailSin = math.sin(self.sailAngle)
        if self.hp>0.3:
            image=self.image
        else:
            image=self.sinkingImage
        if self.burning:
            pygame.draw.line(gameDisplay, (250,100,0), (int(self.x-self.radius*cos),int(self.y-self.radius*sin)),(int(self.x+self.radius*cos),int(self.y+self.radius*sin)),50)
        if(self.angle!=0):
            blitRotate(gameDisplay,image,[self.x,self.y],[self.radius,self.radius],self.angle)
        else:
            gameDisplay.blit(image,(self.x,self.y))
            print("ok")
        if not self.brokenMast:
            pygame.draw.line(gameDisplay, (200,200,150), (int(self.x),int(self.y)),(int(self.x+sailCos*self.radius),int(self.y+sailSin*self.radius)),10)

class Player(Ship):

    def __init__(self, controls):
        super(Player, self).__init__()
        self.x = resolution[0]//2 + random.randint(-300,300)
        self.y = resolution[1]//2 + random.randint(-300,300)
        self.controls = controls

    def inputs(self, pressed):
        if pressed[self.controls["left"]]:# and not self.burning:
            self.angle+=self.speed*0.01
        if pressed[self.controls["right"]]:# and not self.burning:
            self.angle-=self.speed*0.01
        if pressed[self.controls["out"]]:# and not self.brokenMast:
            self.mainsheetAngle+=0.01
        if pressed[self.controls["in"]]:# and not self.brokenMast:
            self.mainsheetAngle-=0.01
        if pressed[self.controls["fire"]] and not self.cooldown:
            self.cooldown=120
            self.shoot()

class Enemy(Ship):

    def __init__(self):
        super(Enemy, self).__init__()
        self.x = random.randint(0,1)*(resolution[0]+100)-50
        self.y = random.random()*resolution[1]
        self.angle = random.random()*math.tau #varning inte 0
        self.speed = -random.random()
        self.mainsheetAngle = math.pi

    def inputs(self, pressed):
        if random.random()>0.5:# and not self.burning:
            self.angle+=self.speed*0.01
        if random.random()>0.5:# and not self.burning:
            self.angle-=self.speed*0.01
        if random.random()>0.5:# and not self.brokenMast:
            self.mainsheetAngle+=0.01
        if random.random()>0.5:# and not self.brokenMast:
            self.mainsheetAngle-=0.01
        if game.players and dist(self, random.choice(game.players))<100 and not self.cooldown:
            self.cooldown=120
            self.shoot()

game = Game()

gameDisplay = pygame.display.set_mode(resolution, pygame.FULLSCREEN)
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                pygame.quit()
                exit()

    game.update()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
exit()