import pygame
import sys
import random, math
import asyncio

BASE_IMAGE_PATH = 'images/'
def load_image(path, color_key=None):
    image = pygame.image.load(BASE_IMAGE_PATH + path)
    if not color_key:
        image = image.convert_alpha()
    else:
        image.set_colorkey(color_key)
    return image

def draw_text(text: str, font: pygame.Font, color: tuple, surf: pygame.Surface, x, y):
    text_obj = font.render(text, 8, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surf.blit(text_obj, text_rect)

def check_circles_collision(pos1, radius1, pos2, radius2):
    v1 = pygame.math.Vector2(pos1)
    v2 = pygame.math.Vector2(pos2)

    # if performance issue, compare squared values of distance and radius instead
    # v1.distance_squared_to(v2) and radii ** 2

    distance = v1.distance_to(v2)

    return distance <= radius1 + radius2

def calculate_angle_from_points_with_math(target_pos, starting_pos):
    dx = target_pos[0] - starting_pos[0]
    dy = target_pos[1] - starting_pos[1]

    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    return angle_radians, angle_degrees

def calculate_direction_from_points_with_vectors(target_pos, starting_pos, wandering=True):
    v1 = pygame.math.Vector2(target_pos)
    v2 = pygame.math.Vector2(starting_pos)

    direction = v1 - v2
    direction = direction.normalize()

    controlled_random_offset = pygame.math.Vector2(
            random.uniform(-0.2, 0.2),
            random.uniform(-0.2, 0.2)
        )

    random_offset = pygame.math.Vector2(
        random.uniform(-0.7, 0.6),
        random.uniform(-0.5, 0.4)
    )
    return direction + random_offset if wandering else direction + controlled_random_offset

class BugManager:
    def __init__(self, image):
        self.image = image
        self.buggies = []   
        #cords                top                       bottom                      left                    right
        self.sides_range = [((0, 800), (-60, -50), 1), ((0, 800), (650, 660), -1), ((-60, -50), (0, 600), 1), ((850, 860), (0, 600), -1)]
        
    def spawn_bug(self):
        chosen_side = random.choice(self.sides_range)
        chosen_pos = [random.randrange(chosen_side[0][0], chosen_side[0][1]), random.randrange(chosen_side[1][0], chosen_side[1][1])]
        value = chosen_side[2]

        dir = calculate_direction_from_points_with_vectors((400, 300), chosen_pos)
        self.buggies.append(Bug(chosen_pos, dir, self.image))

    def count(self):
        return len(self.buggies)

    def update(self, mpos):
        if random.random() < 0.01 and self.count() < 50:
            self.spawn_bug()

        for bug in self.buggies:
            if check_circles_collision(mpos, 50, (bug.pos.x, bug.pos.y), 10): # if mouse and bugs are close enough
                bug.follow_mouse = True
            dead = bug.update(mpos)
            if dead:
                self.buggies.remove(bug)

    def you_can_stop_following_the_mouse_now(self):
        # if all([val for val in bug.follow_mouse for bug in self.buggies]):
        #     return
        for bug in self.buggies:
            bug.follow_mouse = False
            bug.dir = pygame.math.Vector2(random.randrange(-1, 1))

    def render(self, surf):
        for bug in self.buggies:
            bug.render(surf)

class Bug:
    def __init__(self, pos, dir, image: pygame.Surface, speed=6):
        self.pos = pygame.math.Vector2(pos)
        self.dir = dir
        self.speed = speed
        self.follow_mouse = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.timer = 0
        self.timer_2 = 0
        self.transparency = 255
        self.image = image.copy()
        self.rect = self.image.get_frect()
        self.flip = False
        self.grey_image = pygame.transform.grayscale(self.image)
                 
    def update(self, mpos):
        self.timer += 0.05 # timer for sine wave
        self.timer_2 += 0.5 # timer for making the bug disappear

        # follow mouse if triggered 
        if self.follow_mouse:
            self.follow_and_buzz_around(mpos) # should follow mouse around in a soothing kind of way

        if self.dir.x > 0:
            self.flip = True
        elif self.dir.x < 0:
            self.flip = False
        self.pos += self.dir * self.speed
        self.rect.center = self.pos

        if self.timer_2 > 600:
            if self.fade():
                return True
        if self.bug_out_of_bounds():
            return True

    def fade(self):
        self.dir.y += 0.2
        self.transparency = max(0, self.transparency - 5)
        self.image.set_alpha(self.transparency)
        if self.transparency == 0:
            return True
        

    def bug_out_of_bounds(self):
        if self.pos.x < -100 or self.pos.x > 900:
            return True
        if self.pos.y < -100 or self.pos.y > 700:
            return True
        return False

    def follow_and_buzz_around(self, target):
        # TODO: make it look good
        if check_circles_collision(target, 50, self.pos, 10):
            # idle
            self.dir = pygame.math.Vector2(0, math.sin(round(self.timer, 2)) * 0.5)
        elif not check_circles_collision(target, 50, self.pos, 30):
            self.dir = calculate_direction_from_points_with_vectors(target, self.pos, False)

    def render(self, surf):
        if self.follow_mouse:
            surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        else:
            surf.blit(pygame.transform.flip(self.grey_image, self.flip, False), self.rect)

class UI:
    def __init__(self, font):
        self.count_down = 30
        self.number_of_buggies = 0
        self.points = 0
        self.font = font

    def update(self):
        if self.count_down == 0:
            return True # game over

    def calc_points(self):
        if self.count_down:
            self.points += self.number_of_buggies

    def restart(self):
        self.count_down = 30
        self.number_of_buggies = 0
        self.points = 0

    def render_grade(self, surf):
        # TODO: replace with images
        if self.points > 122:
            color = (0, 255, 0)
        else:
            color = (255, 255, 255)
        draw_text('your score', self.font, ((255, 255, 255)), surf, 300, 100)
        draw_text(str(self.points), self.font, color, surf, 360, 300)
        draw_text("Press Any Button to restart", self.font, ((255, 255, 255)), surf, 270, 500)
        
    def render(self, surf):
        draw_text(str(self.count_down), self.font, ((255, 255, 255)), surf, 400, 10)

class BG:
    def __init__(self, image):
        self.image = image
        self.image_size = self.image.get_size()
        self.background_offset = [0, 1]
        self.images_loc = [
            [0, 0],
            # [0 + self.image_size[0], 0],
            [0, 0 + self.image_size[1]],
            # [0 + self.image_size[0], 0 + self.image_size[1]]
        ]   

    def update(self):
        for i in range(len(self.images_loc)):
            self.images_loc[i][0] -= self.background_offset[0]
            self.images_loc[i][1] -= self.background_offset[1]

            if self.images_loc[i][1] < -self.image_size[1]:
                self.images_loc[i][1] = 0 + self.image_size[1]
            


    def render(self, surf):
        for loc in self.images_loc:
            surf.blit(self.image, (loc[0], loc[1]))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('Busy Bees')
        self.clock = pygame.time.Clock()

        self.assets = {
            'bee': load_image('bee.png', (255,255,255)),
            'bg': load_image('bg.png'),
            # 'title_card': load_image('title.png'),
            'play': pygame.transform.scale_by(load_image('play.png'), 0.5),
            'sad-bee': load_image('bee-sad.png', (255, 255, 255))
        }
        self.font = pygame.font.SysFont("sans", 36)
        self.bg = BG(self.assets['bg'])
        self.button_rect = self.assets['play'].get_rect()
        self.bug_manager = BugManager(self.assets['bee'])
        self.running = True
        self.trans_surf = pygame.Surface((800, 600))
        self.trans_surf.fill((0, 0, 0))
        self.trans_surf.set_alpha(150)
        self.main_menu = True
        self.button_rect.center = (400, 300)

        self.ui = UI(self.font)

        self.next_second = pygame.time.get_ticks() + 1000

    def manage_bg_system(self):
        self.screen.blit(self.assets['bg'], (0 + self.background_offset[0], 0 + self.background_offset[1]))
        self.background_offset[0] += 1

    def game_over(self):
        self.screen.blit(self.trans_surf)
        self.ui.render_grade(self.screen)     

    def restart(self):
        self.ui.restart()

    async def run(self):
        while self.main_menu:
            self.screen.fill((100, 100, 100))

            mpos = pygame.mouse.get_pos()

            # menu
            self.bg.update()
            self.bg.render(self.screen)

            self.screen.blit(self.assets['play'], self.button_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and self.button_rect.collidepoint(mpos):
                    self.main_menu = False
                    self.running = True

            pygame.display.flip()
            await asyncio.sleep(0)
            self.clock.tick(60)

        while self.running:
            self.screen.fill((0, 0, 0))
            self.bg.update()
            self.bg.render(self.screen)

            mpos = pygame.mouse.get_pos()


            self.bug_manager.update(mpos)
            self.bug_manager.render(self.screen)

            self.ui.render(self.screen)

            if self.ui.count_down == 0:
                self.game_over()
                self.bug_manager.you_can_stop_following_the_mouse_now()

            self.ui.number_of_buggies = self.bug_manager.count()

            current_time = pygame.time.get_ticks()
            if current_time >= self.next_second:
                self.ui.count_down = max(0, self.ui.count_down - 1)
                self.ui.calc_points()
                self.next_second = pygame.time.get_ticks() + 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.ui.count_down == 0:
                        self.restart()
       
            pygame.display.flip()
            await asyncio.sleep(0)
            self.clock.tick(60)


asyncio.run(Game().run())
