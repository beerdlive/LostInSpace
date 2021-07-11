import pygame
import os
import random
import csv
import button
from pygame.sprite import Sprite

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lost In Space")

# set framerate
clock = pygame.time.Clock()
FPS = 60

# define game variables
GRAVITY = 0.75
SCROLL_THRESH = 400
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 2
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False

# define player action variables
moving_left = False
moving_right = False
shoot = False

# load images
# button images
start_img = pygame.image.load('images/start_btn.png').convert_alpha()
exit_img = pygame.image.load('images/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('images/restart_btn.png').convert_alpha()
# background
pine1_img = pygame.image.load('images/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('images/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('images/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('images/background/sky_cloud.png').convert_alpha()
# store tiles in list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'images/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
# bullet
bullet_img = pygame.image.load('images/icons/bullet_img.png').convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (int(bullet_img.get_width() * 1.5),
                                                 (int(bullet_img.get_height() * 1.5))))

# enemy1 bullet
enemy1_bullet_img = pygame.image.load('images/icons/enemy1_bullet_img.png').convert_alpha()
enemy1_bullet_img = pygame.transform.scale(enemy1_bullet_img, (int(enemy1_bullet_img.get_width()),
                                                        (int(enemy1_bullet_img.get_height()))))

# enemy2 bullet
enemy2_bullet_img = pygame.image.load('images/icons/enemy2_bullet_img.png').convert_alpha()
enemy2_bullet_img = pygame.transform.scale(enemy2_bullet_img, (int(enemy2_bullet_img.get_width() * 2.5),
                                                        (int(enemy2_bullet_img.get_height() * 2.5))))

# enemy3 bullet
enemy3_bullet_img = pygame.image.load('images/icons/enemy3_bullet_img.png').convert_alpha()
enemy3_bullet_img = pygame.transform.scale(enemy3_bullet_img, (int(enemy3_bullet_img.get_width() * 1.5),
                                                        (int(enemy3_bullet_img.get_height() * 1.5))))

# define colors
BG = (0, 0, 20)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# define font
font = pygame.font.SysFont('Asphalt', 30)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(6):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    enemy1_bullet_group.empty()
    enemy2_bullet_group.empty()
    decoration_group.empty()
    lava_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data

class Character(Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.shoot_cooldown = 0
        self.health = health
        self.max_health = 100
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Attack', 'Death']
        for animation in animation_types:
            # reset temporary list of images
            temp_list = []
            # count num of files in the folder
            num_of_frames = len(os.listdir(f'images/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'images/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), (int(img.get_height() * scale))))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0

        # assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump is True and self.in_air is False:
            self.vel_y = -12.5
            self.jump = False
            self.in_air = True

        # apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        # check collision
        for tile in world.obstacle_list:
            # check collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                # if the ai has hit a wall, turn around
                if self.char_type == 'enemy1' or 'enemy2' or 'enemy3':
                    self.direction *= -1
                    self.move_counter = 0
            # check collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below the ground, jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # check for collision with water
        if pygame.sprite.spritecollide(self, lava_group, False):
            self.health = 0

        # check for exit collision
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # check if fallen off map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # check if going off edge
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        # update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll <
                    (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                        or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)

    def enemy1_shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 10
            bullet = EnemyBullet(self.rect.centerx + (self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            enemy1_bullet_group.add(bullet)

    def enemy2_shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 60
            bullet = EnemyBullet2(self.rect.centerx + (self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            enemy2_bullet_group.add(bullet)

    def enemy3_shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 60
            bullet = EnemyBullet3(self.rect.centerx + (self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            enemy3_bullet_group.add(bullet)

    def ai(self):
        if self.char_type == 'enemy1':  # short enemy
            if self.alive and player.alive:
                if self.idling is False and random.randint(1, 10) == 1:
                    self.update_action(2)  # 0 is Idle
                    self.jump = True
                    self.idling_counter = 50
                # check if ai is near player
                if self.vision.colliderect(player.rect):
                    # stop running and face player
                    self.update_action(0)  # 0 is Idle
                    # shoot
                    self.enemy1_shoot()
                else:
                    if self.idling is False:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)  # 1 for Run
                        self.move_counter += 1
                        # update ai vision as enemy moves
                        self.vision.center = (self.rect.centerx + 50 * self.direction, self.rect.centery)

                        if self.move_counter > TILE_SIZE:
                            self.direction *= -1
                            self.move_counter *= -1
                    else:
                        self.idling_counter -= 1
                        if self.idling_counter <= 0:
                            self.idling = False
            # scroll
            self.rect.x += screen_scroll

        elif self.char_type == 'enemy2':  # plant enemy
            if self.alive and player.alive:
                if self.idling is False and random.randint(1, 200) == 1:
                    self.update_action(0)  # 0 is Idle
                    self.idling = True
                    self.idling_counter = 50
                # check if ai is near player
                if self.vision.colliderect(player.rect):
                    # stop running and face player
                    self.update_action(0)  # 0 is Idle
                    # shoot
                    self.enemy2_shoot()
                else:
                    if self.idling is False:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)  # 1 for Run
                        self.move_counter += 1
                        # update ai vision as enemy moves
                        self.vision.center = (self.rect.centerx + 200 * self.direction, self.rect.centery)

                        if self.move_counter > TILE_SIZE:
                            self.direction *= -1
                            self.move_counter *= -1
                    else:
                        self.idling_counter -= 1
                        if self.idling_counter <= 0:
                            self.idling = False
            # scroll
            self.rect.x += screen_scroll

        else:  # bird enemy
            if self.alive and player.alive:
                if self.idling is False and random.randint(1, 200) == 1:
                    self.update_action(0)  # 0 is Idle
                    self.idling = True
                    self.idling_counter = 50
                # check if ai is near player
                if self.vision.colliderect(player.rect):
                    # stop running and face player
                    self.update_action(0)  # 0 is Idle
                    # shoot
                    self.enemy3_shoot()
                else:
                    if self.idling is False:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)  # 1 for Run
                        self.move_counter += 1
                        # update ai vision as enemy moves
                        self.vision.center = (self.rect.centerx + 150 * self.direction, self.rect.centery)

                        if self.move_counter > TILE_SIZE:
                            self.direction *= -1
                            self.move_counter *= -1
                    else:
                        self.idling_counter -= 1
                        if self.idling_counter <= 0:
                            self.idling = False
            # scroll
            self.rect.x += screen_scroll


    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # if animation has run out then reset back to start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 4:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # check if the new action is different than previous
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(4)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        lava = Lava(img, x * TILE_SIZE, y * TILE_SIZE)
                        lava_group.add(lava)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:  # create player
                        player = Character('player', x * TILE_SIZE, y * TILE_SIZE, 2, 5, 100)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:
                        enemy = Character('enemy1', x * TILE_SIZE, y * TILE_SIZE, 2, 7, 25)
                        enemy_group.add(enemy)
                    elif tile == 17:
                        enemy = Character('enemy2', x * TILE_SIZE, y * TILE_SIZE, 2, 0, 100)
                        enemy_group.add(enemy)
                    elif tile == 18:
                        enemy = Character('enemy3', x * TILE_SIZE, y * TILE_SIZE, 2, 4, 50)
                        enemy_group.add(enemy)
                    elif tile == 19:  # health
                        pass
                    elif tile == 20:  # create exit
                        exit1 = ExitLevel(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit1)
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

class Decoration(Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Lava(Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ExitLevel(Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # update with new health
        self.health = health
        # calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        # check collision with characters
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()


class EnemyBullet(Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 7
        self.image = enemy1_bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # check collision with characters
        if pygame.sprite.spritecollide(player, enemy1_bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()


class EnemyBullet2(Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 1
        self.image = enemy2_bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # check collision with characters
        if pygame.sprite.spritecollide(player, enemy2_bullet_group, False):
            if player.alive:
                player.health -= 25
                self.kill()


class EnemyBullet3(Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 4
        self.image = enemy3_bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # check collision with characters
        if pygame.sprite.spritecollide(player, enemy3_bullet_group, False):
            if player.alive:
                player.health -= 20
                self.kill()


# create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy1_bullet_group = pygame.sprite.Group()
enemy2_bullet_group = pygame.sprite.Group()
enemy3_bullet_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


# create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
# load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)


run = True
while run:

    clock.tick(FPS)

    if start_game is False:
        # draw menu
        screen.fill(BG)
        # add buttons
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
    else:
        # update background
        draw_bg()
        # draw world map
        world.draw()
        # show health
        health_bar.draw(player.health)

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # update and draw groups
        enemy1_bullet_group.update()
        enemy2_bullet_group.update()
        enemy3_bullet_group.update()
        bullet_group.update()
        decoration_group.update()
        lava_group.update()
        exit_group.update()
        enemy1_bullet_group.draw(screen)
        enemy2_bullet_group.draw(screen)
        enemy3_bullet_group.draw(screen)
        bullet_group.draw(screen)
        decoration_group.draw(screen)
        lava_group.draw(screen)
        exit_group.draw(screen)

        # update player actions
        if player.alive:
            # shoot bullets
            if shoot:
                player.shoot()
            if player.in_air:
                player.update_action(2)  # 2 means jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1 means run
            else:
                player.update_action(0)  # 0 means idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if level complete
            if level_complete:
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    # load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
                else:
                    run = False
        else:
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = reset_level()
                # load in level data and create world
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)

    for event in pygame.event.get():
        # quit
        if event.type == pygame.QUIT:
            run = False

        # keyboard pressed
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False

        # keyboard released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False

    pygame.display.update()

pygame.quit()
