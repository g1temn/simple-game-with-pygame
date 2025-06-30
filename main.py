import pygame, random, datetime, os

seconds = 0
minutes = 0
hours = 0
timer_text = "Game time: 00:00:00"
file_path = "best_score.txt"

def get_current_time():
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    return f"Current time: {current_time}"

def update_timer():
    if not game_over:
        global seconds, minutes, hours, timer_text
        seconds += 1
        if seconds >= 60:
            minutes += 1
            seconds = 0
        if minutes >= 60:
            minutes = 0
            hours += 1
        
        timer_text = f"Game time: {hours:02}:{minutes:02}:{seconds:02}"

GAME_WIDTH, GAME_HEIGHT = 500, 500
fps = 60

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Simple Game")
game_window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
clock = pygame.time.Clock()
spawning_delay = 1500
reload_delay = 700
kills = 0

if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        try:
            best_score = int(file.read())
        except ValueError:
            best_score = 0
else: best_score = 0

game_over = True
is_in_menu = True

def show_text(text: str, color, x, y, size):
    font = pygame.font.SysFont("Comic Sans Ms", size)
    text_render = font.render(text, True, color)
    game_window.blit(text_render, (x, y))

#sounds
selection_sound = pygame.mixer.Sound('sounds/selection.wav')
autoreload_sound = pygame.mixer.Sound('sounds/autoreload.mp3')
shot_sounds = [pygame.mixer.Sound('sounds/shot sound 1.wav'),
               pygame.mixer.Sound('sounds/shot sound 2.wav'),
               pygame.mixer.Sound('sounds/shot sound 3.wav'),
               pygame.mixer.Sound('sounds/shot sound 4.wav'),
               pygame.mixer.Sound('sounds/shot sound 5.wav'),
               pygame.mixer.Sound('sounds/shot sound 6.wav'),
               pygame.mixer.Sound('sounds/shot sound 7.wav')]
running_sound = pygame.mixer.Sound('sounds/running.mp3')
healing_sound = pygame.mixer.Sound('sounds/healing.mp3')
reload_sound = pygame.mixer.Sound('sounds/gun reload.mp3')
game_over_music = pygame.mixer.Sound('sounds/game over screen.mp3')
game_music = pygame.mixer.Sound('sounds/game music.mp3')
menu_music = pygame.mixer.Sound('sounds/menu music.mp3')
collision_sound = pygame.mixer.Sound('sounds/collision.wav')
getting_damage_sound = pygame.mixer.Sound('sounds/getting damage.wav')
score_sound = pygame.mixer.Sound('sounds/score.mp3')

def play_sound(sound, volume, loop=0):
    sound.set_volume(volume)
    sound.play(loop)

play_sound(menu_music, 0.05, -1)

def switch_bg_music(bg_music, loop=-1):
    pygame.mixer.stop()
    play_sound(bg_music, 0.05, loop)

#images
bg_image = pygame.image.load('images/bg.png')
bg_image = pygame.transform.scale(bg_image, (GAME_WIDTH, GAME_HEIGHT))

player_image = pygame.image.load('images/player.png')
player_image = pygame.transform.scale(player_image, (40, 40))

enemy_image = pygame.image.load('images/enemy.png')
enemy_image = pygame.transform.scale(enemy_image, (40, 40))

shooting_image = pygame.image.load('images/shooting.png')
shooting_image = pygame.transform.scale(shooting_image, (30, 30))

basic_cursor_image = pygame.image.load('images/basic cursor.png')
basic_cursor_image = pygame.transform.scale(basic_cursor_image, (30, 30))

pygame.mouse.set_visible(False)

blood_image = pygame.image.load('images/blood.png')
blood_image = pygame.transform.scale(blood_image, (GAME_WIDTH, GAME_HEIGHT))

is_blood_drawn = False

hp_kit_image = pygame.image.load('images/hp kit.png')
hp_kit_image = pygame.transform.scale(hp_kit_image, (35, 35))

bullets_kit_image = pygame.image.load('images/bullets kit.png')
bullets_kit_image = pygame.transform.scale(bullets_kit_image, (35, 35))

start_btn_image = pygame.image.load('images/start btn.png')
menu_btn_image = pygame.image.load('images/menu btn.png')

class Button(pygame.Rect):
    def __init__(self, x, y, image, scale):
        self.image = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self):
        game_window.blit(self.image, self.rect.topleft)

    def get_clicked(self):
        action = False

        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0] and not self.clicked:
                self.clicked = True
                action = True
                play_sound(selection_sound, 0.07)

        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False

        return action

start_btn = Button(75, GAME_HEIGHT/2 + 50, start_btn_image, 0.75)
menu_btn = Button(180, GAME_HEIGHT/2 + 65, menu_btn_image, 0.75)

def replace_pointer(image):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    game_window.blit(image, (mouse_x - image.get_width()/4, mouse_y - image.get_height()/4))

def splash_image(image):
    game_window.blit(image, (0, 0))

player_spawn_x = (GAME_WIDTH/2)-20
player_spawn_y = (GAME_HEIGHT/2)-20

#general character class
class Character(pygame.Rect):
    def __init__(self, image, hp, damage, speed, x, y):
        super().__init__(x, y, 40, 40)
        self.image = image
        self.hp = hp
        self.damage = damage
        self.speed = speed
        self.original_image = image

    def draw(self):
        game_window.blit(self.image, (self.x, self.y))

    def show_health_bar(self, x, y, K):
        width = K * self.hp
        pygame.draw.rect(game_window, "green", (x, y, width, 10))

    def get_damage(self, damage):
        self.hp -= damage

class Player(Character):
    def __init__(self, image, hp, damage, speed, x, y):
        super().__init__(image, hp, damage, speed, x, y)
        self.last_shot_time = 0
        self.cd = 200 # 200 ms time gap between each bullet shooting 
                      # "cooldown" time
        self.bullets = 6
        self.max_bullets = 6
        self.max_hp = 100

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

        if keys in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s]:
            return True

    def attack(self):
        current_time = pygame.time.get_ticks()

        if pygame.mouse.get_pressed()[0] and current_time - self.last_shot_time >= self.cd and self.bullets > 0:
            #print('attack!!')
            bullet = Bullet(color="grey",
                            speed=10)
            
            bullets.append(bullet)
            self.last_shot_time = current_time
            self.bullets -= 1
            play_sound(random.choice(shot_sounds), 0.3)

    def show_bullet_bar(self, x, y):
        width = self.bullets * 10
        pygame.draw.rect(game_window, '#33e8eb', (x, y, width, 10))
    
    def get_killed(self):
        if self.hp <= 0:
            global game_over
            game_over = True
            switch_bg_music(game_over_music, 0)

    def follow_mouse_dir(self):
        direction = pygame.Vector2(pygame.mouse.get_pos()) - pygame.Vector2(self.center)
        rad, angle = direction.as_polar()
        rotated_image = pygame.transform.rotate(self.original_image, -angle)
        self.image = rotated_image
        self.rect = self.image.get_rect(center=self.center)
            
player = Player(image=player_image, 
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
    def __init__(self, color, speed):
        super().__init__(player.x + (player.width/4), player.y + (player.height/4), 20, 20)
        self.color = color
        self.speed = speed
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

loot_list = []
def handle_loot():
    for loot_item in loot_list:
        loot_item.draw()
        loot_item.collide(player)

class Loot(pygame.Rect):
    def __init__(self, x, y, image, purpose):
        super().__init__(x, y, 35, 35)
        self.image = image
        self.purpose = purpose

    def draw(self):
        game_window.blit(self.image, (self.x, self.y))

    def collide(self, target):
        if self.colliderect(target):
            match self.purpose:
                case "hp":
                    if target.hp < 100:
                        target.hp = target.max_hp
                        loot_list.remove(self)
                        play_sound(healing_sound, 0.5)
                case "bullets":
                    if target.bullets < target.max_bullets:
                        target.bullets = target.max_bullets
                        loot_list.remove(self)
                        play_sound(reload_sound, 0.5)

enemies = []
class Enemy(Character):
    def __init__(self, image, hp, damage, speed, x, y):
        super().__init__(image, hp, damage, speed, x, y)
        self.pos = pygame.Vector2(x, y)
        self.knockback_frames = 0
        self.can_attack = True
        self.possible_loot = ["hp", "bullets", "bullets", "bullets", "n", "n", "n", "n", "n", "n"]

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
        global is_blood_drawn
        if self.knockback_frames > 0:
            self.knockback_frames -= 1
            self.can_attack = False
            if not is_blood_drawn: splash_image(blood_image)
            is_blood_drawn = True
            self.direction = pygame.Vector2(self.x - object.x, self.y - object.y)
        else:
            is_blood_drawn = False
            self.can_attack = True
            self.direction = pygame.Vector2(object.x - self.x, object.y - self.y)

        if self.direction.length() != 0:
            self.direction = self.direction.normalize()
        else:
            self.direction = pygame.Vector2(0, 0)
            
        self.pos += self.direction * self.speed
        self.x = int(self.pos.x)
        self.y = int(self.pos.y)

    def bite(self, object):
        if self.colliderect(object) and self.can_attack:
            object.get_damage(self.damage)
            play_sound(getting_damage_sound, 0.4)
            self.knockback_frames = 30

    def drop_loot(self):
        if len(loot_list) < 5:
            loot = random.choice(self.possible_loot)
            match loot:
                case "hp":
                    hp_kit_loot = Loot(self.x, self.y, hp_kit_image, "hp")
                    loot_list.append(hp_kit_loot)
                case "bullets":
                    bullets_kit_loot = Loot(self.x, self.y, bullets_kit_image, "bullets")
                    loot_list.append(bullets_kit_loot)
                case "n": # nothing
                    pass

    def follow_player_dir(self):
        direction = pygame.Vector2(player.center) - pygame.Vector2(self.center)
        rad, angle = direction.as_polar()
        rotated_image = pygame.transform.rotate(self.original_image, -angle)
        self.image = rotated_image
        self.rect = self.image.get_rect(center=self.center)

def create_enemy():
    enemy = Enemy(image=enemy_image,
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
        enemy.follow_player_dir()
        enemy.bite(player)
        enemy.show_health_bar(enemy.x - 10, enemy.y - 20, 1.2)

        if enemy.hp <= 0:
            enemy.drop_loot()
            enemies.remove(enemy)
            global kills
            kills += 1
            play_sound(score_sound, 0.3)

        for bullet in bullets[:]:
            if bullet.colliderect(enemy):
                bullet.enemy_collision = True
                enemy.get_damage(player.damage)
                play_sound(collision_sound, 0.4)

def add_bullet(player):
    if player.bullets < player.max_bullets:
        play_sound(autoreload_sound, 0.04)
        player.bullets += 1

def restart_game():
    global player_spawn_x, player_spawn_y, game_over
    global seconds, minutes, hours, timer_text
    global kills, best_score, player

    player.x = player_spawn_x
    player.y = player_spawn_y
    player.hp = 100
    player.bullets = player.max_bullets
    player.last_shot_time = 0

    seconds, minutes, hours = 0, 0, 0
    
    bullets.clear()
    enemies.clear()
    loot_list.clear()

    timer_text = "Game time: 00:00:00"
    kills = 0

    game_over = False

def upgrade_best_score():
    global best_score, kills
    if kills > best_score:
        with open(file_path, 'w') as file:
            best_score = kills
            file.write(str(best_score))

def show_menu():
    restart_game()
    start_btn.draw()

    global is_in_menu, game_over
    if start_btn.get_clicked():
        switch_bg_music(game_music)
        is_in_menu = False
        game_over = False

    show_text("MAN-SURVIVOR", "gold", 45, GAME_HEIGHT/2 - 190, 50)
    show_text("Version 1.0.4", "darkred", 160, GAME_HEIGHT/2 - 120, 30)
    player.show_health_bar(player.x - 10, player.y - 32, 0.6)
    player.show_bullet_bar(player.x - 10, player.y - 20)
    player.follow_mouse_dir()
    show_text(str(int(kills)), "red", player.x + 55, player.y - 35, 20)
    player.draw()
    replace_pointer(basic_cursor_image)

def show_game():
    render_bullets()
    handle_loot()
    player.draw()
    player.follow_mouse_dir()
    handle_enemies()
    
    player.move()
    player.attack()
    player.get_killed()

    player.show_health_bar(player.x - 10, player.y - 32, 0.6)
    player.show_bullet_bar(player.x - 10, player.y - 20)
    show_text(str(int(kills)), "red", player.x + 55, player.y - 35, 20)

    show_text(get_current_time(), "black", 10, 10, 20)
    show_text(timer_text, "black", 10, 30, 20)

    replace_pointer(shooting_image)

def show_game_over():
    menu_btn.draw()
    global is_in_menu, game_over

    if menu_btn.get_clicked():
        switch_bg_music(menu_music)
        is_in_menu = True
        game_over = True

    show_text("GAME OVER", "red", 40, GAME_HEIGHT/2 - 150, 70)
    show_text("Hit 'Space' to start new round...", "green", 30, GAME_HEIGHT/2 - 65, 30)
    show_text(timer_text, "black", 40, GAME_HEIGHT/2 - 20, 20)
    show_text(f"Kills: {kills}", "black", 40, GAME_HEIGHT/2, 20)
    show_text(f"Best score: {best_score}", "black", 40, GAME_HEIGHT/2 + 20, 20)
    replace_pointer(basic_cursor_image)
    upgrade_best_score()

spawn_enemy = pygame.USEREVENT
pygame.time.set_timer(spawn_enemy, spawning_delay)

add_bullet_event = pygame.USEREVENT + 1
pygame.time.set_timer(add_bullet_event, reload_delay)

update_timer_event = pygame.USEREVENT + 2
pygame.time.set_timer(update_timer_event, 1000)

running = True
while running: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            upgrade_best_score()
            running = False
        if event.type == spawn_enemy and not is_in_menu and not game_over:
            create_enemy()
        if event.type == add_bullet_event and not is_in_menu and not game_over:
            add_bullet(player)
        if event.type == update_timer_event and not is_in_menu and not game_over:
            update_timer()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_over and not is_in_menu:
            switch_bg_music(game_music)
            restart_game()

    game_window.blit(bg_image, (0, 0))

    #print(f'enemies: {len(enemies)} and bullets: {len(bullets)}')
    if not game_over and not is_in_menu:
        show_game()
    elif game_over and not is_in_menu:
        show_game_over()
    else:
        show_menu()

    pygame.display.update()
    clock.tick(fps)

pygame.quit()