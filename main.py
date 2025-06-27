import pygame
import random

GAME_WIDTH, GAME_HEIGHT = 500, 500
fps = 60

pygame.init()
pygame.display.set_caption("Simple Game")
game_window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
clock = pygame.time.Clock()
spawning_delay = 1500

#images
shooting_image = pygame.image.load('images/shooting.png')
shooting_image = pygame.transform.scale(shooting_image, (30, 30))
pygame.mouse.set_visible(False)

def replace_pointer(image):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    game_window.blit(image, (mouse_x - image.get_width()/4, mouse_y - image.get_height()/4))

player_spawn_x = (GAME_WIDTH/2)-20
player_spawn_y = (GAME_HEIGHT/2)-20

#general character class
class Character(pygame.Rect):
    def __init__(self, color, hp, damage, speed, x, y):
        super().__init__(x, y, 40, 40)
        self.color = color
        self.hp = hp
        self.damage = damage
        self.speed = speed

    def draw(self):
        pygame.draw.rect(game_window, self.color, self)

    def get_damage(self, damage):
        self.hp -= damage

class Player(Character):
    def __init__(self, color, hp, damage, speed, x, y):
        super().__init__(color, hp, damage, speed, x, y)
        self.last_shot_time = 0
        self.cd = 200 # 200 ms time gap between each bullet shooting 
                      # "cooldown" time
    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_d] and self.x + self.width < GAME_WIDTH:
            self.x += self.speed
        if keys[pygame.K_w] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_s] and self.y + self.height < GAME_HEIGHT:
            self.y += self.speed

    def attack(self):
        current_time = pygame.time.get_ticks()

        if pygame.mouse.get_pressed()[0] and current_time - self.last_shot_time >= self.cd:
            #print('attack!!')
            bullet = Bullet(color="green",
                            speed=10,
                            attack=50)
            
            bullets.append(bullet)
            self.last_shot_time = current_time
            
player = Player(color="blue", 
                hp=100, 
                damage=25, 
                speed=5,
                x=player_spawn_x,
                y=player_spawn_y)

bullets = []
def render_bullets():
    for bullet in bullets:
        bullet.draw()
        bullet.fly()

        if bullet.x + bullet.width < 0 or bullet.x > GAME_WIDTH or bullet.y + bullet.height < 0 or bullet.y > GAME_HEIGHT or bullet.enemy_collision:
            bullets.remove(bullet)

class Bullet(pygame.Rect):
    def __init__(self, color, speed, attack):
        super().__init__(player.x + (player.width/4), player.y + (player.height/4), 20, 20)
        self.color = color
        self.speed = speed
        self.attack = attack
        self.pos = pygame.Vector2(self.x, self.y)
        self.enemy_collision = False

        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.direction = pygame.Vector2(mouse_x - self.x, mouse_y - self.y)
        if self.direction.length() != 0:
            self.direction = self.direction.normalize()

    def draw(self):
        pygame.draw.rect(game_window, self.color, self)

    def fly(self):
        self.pos += self.direction * self.speed
        self.x = int(self.pos.x)
        self.y = int(self.pos.y)

enemies = []
class Enemy(Character):
    def __init__(self, color, hp, damage, speed, x, y):
        super().__init__(color, hp, damage, speed, x, y)
        self.pos = pygame.Vector2(x, y)

    def spawn(self):
        side = random.choice(["left", "right", "top", "bottom"])
        match side:
            case "left":
                self.x = -self.width
                self.y = random.randint(0, GAME_HEIGHT - self.height)
            case "right":
                self.x = GAME_WIDTH
                self.y = random.randint(0, GAME_HEIGHT - self.height)
            case "top":
                self.x = random.randint(0, GAME_WIDTH - self.width)
                self.y = -self.height
            case "bottom":
                self.x = random.randint(0, GAME_WIDTH - self.width)
                self.y = GAME_HEIGHT

        self.pos = pygame.Vector2(self.x, self.y)


    def chase(self, object):
        self.direction = pygame.Vector2(object.x - self.x, object.y - self.y)
        if self.direction.length() != 0:
            self.direction = self.direction.normalize()
        else:
            self.direction = pygame.Vector2(0, 0)
        self.pos += self.direction * self.speed
        self.x = int(self.pos.x)
        self.y = int(self.pos.y)

    def bite(self):
        ...

def create_enemy():
    enemy = Enemy(color="red",
                  hp=50,
                  damage=25,
                  speed=3,
                  x=0,
                  y=0)
    enemy.spawn()
    enemies.append(enemy)

def handle_enemies():
    for enemy in enemies:
        enemy.draw()
        enemy.chase(player)
        
        for bullet in bullets:
            if bullet.colliderect(enemy):
                bullet.enemy_collision = True
                enemies.remove(enemy)

spawn_enemy = pygame.USEREVENT
pygame.time.set_timer(spawn_enemy, spawning_delay)

running = True
while running: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == spawn_enemy:
            create_enemy()

    game_window.fill('white')

    #print(f'enemies: {len(enemies)} and bullets: {len(bullets)}')

    player.move()
    player.attack()
    render_bullets()
    handle_enemies()
    player.draw()
    replace_pointer(shooting_image)

    pygame.display.update()
    clock.tick(fps)

pygame.quit()