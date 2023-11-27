from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Union
import math
import random
import heapq
from collections import deque

import pygame
import pygame.freetype
from pygame import Vector2, Surface

# reference from picture in pixels
REFERENCE_SCREEN_SIZE = 885
REFERENCE_ROTATOR_SIZE = 285
REFERENCE_ROTATOR_INNER_SIZE = 26
REFERENCE_PLAYER_SIZE = 45
REFERENCE_PLAYER_SPHERE_DISTANCE = 63.15
REFERENCE_SPHERE_SIZE = 33
REFERENCE_BURST_OUTER_SIZE = 59
REFERENCE_BURST_INNER_SIZE = 41

# part of screen
ROTATOR_SIZE = REFERENCE_ROTATOR_SIZE / REFERENCE_SCREEN_SIZE / 2
ROTATOR_INNER_SIZE = REFERENCE_ROTATOR_INNER_SIZE / REFERENCE_SCREEN_SIZE / 2
PLAYER_SIZE = REFERENCE_PLAYER_SIZE / REFERENCE_SCREEN_SIZE / 2
SPHERE_SIZE = REFERENCE_SPHERE_SIZE / REFERENCE_SCREEN_SIZE / 2



DEFAULT_SPEED = 2 / 400
# SPHERE_SIZE = 7
# PLAYER_SIZE = 10

class Team(Enum):
    RED = (255, 90, 40)
    GREEN = (40, 255, 40)
    BLUE = (63, 80, 255)
    DARKRED = (190, 0, 0)
    DARKGREEN = (25, 93, 42)

    YELLOW = (255, 255, 40)
    PINK = (255, 40, 255)
    SKY = (40, 255, 255)
    PURPLE = (142, 70, 172)

    ORANGE = (255, 130, 1)
    BROWN = (128, 64, 64)
    INDIGO = (70, 0, 148)

color_names = {
    team.value: name for team, name in zip(Team, [
        'Red', 'Green', 'Blue', 'Dark red', 'Dark green', 'Yellow', 'Pink', 'Sky', 'Purple', 'Orange', 'Brown', 'Indigo'
    ])
}

@dataclass
class VerticalLine:
    x: float
@dataclass
class HorizontalLine:
    y: float

@dataclass
class Ray:
    origin: Vector2
    direction: Vector2
    def intersects(self, other: 'Ray'):
        if not isinstance(other, Ray):
            raise TypeError('other thing must be Ray')
        det = self.direction.x * other.direction.y - other.direction.x * self.direction.y
        if det == 0:
            return None  # Rays are parallel, no intersection

        diff_origin = other.origin - self.origin
        t = (diff_origin.x * other.direction.y - diff_origin.y * other.direction.x) / det
        u = (diff_origin.x * self.direction.y - diff_origin.y * self.direction.x) / det
        if t < 0 or u < 0:
            return None  # Intersection point is behind one of the rays

        intersection_point = self.origin + self.direction * t
        distance = self.origin.distance_to(intersection_point)
        return distance

    def intersects_sphere(self, sphere: 'Sphere'):
        # https://math.stackexchange.com/a/4785487
        diff = sphere.center - self.origin
        dir = self.direction.normalize()
        cx = dir.x * diff.x + dir.y * diff.y
        cy = -dir.y * diff.x + dir.x * diff.y
        if cx > 0 and -sphere.radius <= cy <= sphere.radius:
            return cx
        else:
            return None

@dataclass
class Sphere:
    center: Vector2
    velocity: Vector2
    radius: float
    color: tuple[int, int, int] = (255, 255, 255)
    mass: float = 1
    damping_factor: float = 1

    def get_rect(self):
        return self.center.x-self.radius, self.center.y-self.radius, self.radius*2, self.radius*2
    def get_ray(self):
        return Ray(self.center, self.velocity)

    def intersects(self, other: Union['Sphere', VerticalLine, HorizontalLine]):
        if isinstance(other, Sphere):
            return self.center.distance_squared_to(other.center) <= (self.radius + other.radius) ** 2
        if isinstance(other, VerticalLine):
            return other.x - self.radius < self.center.x < other.x + self.radius
        if isinstance(other, HorizontalLine):
            return other.y - self.radius < self.center.y < other.y + self.radius
        raise TypeError('Can check collisions only with Sphere, VerticalLine and HorizontalLine for now')

    def will_hit_sphere(self, other: 'Sphere'):
        # Calculate the time until the spheres will intersect
        relative_velocity = self.velocity - other.velocity
        relative_position = self.center - other.center
        a = relative_velocity.magnitude_squared()
        b = 2 * relative_velocity.dot(relative_position)
        c = relative_position.magnitude_squared() - (self.radius + other.radius)**2
        discriminant = b**2 - 4*a*c

        if discriminant < 0:
            return None  # The spheres will never intersect

        # Calculate the time at which the spheres will intersect
        t = (-b - math.sqrt(discriminant)) / (2*a)
        if t < 0:
            return None  # The spheres have already passed each other

        return t  # The spheres will eventually collide

        # return time_to_collision if time_to_collision >= 0 else None

    def check_center_inside(self, other: 'Sphere'):
        if isinstance(other, Sphere):
            return self.center.distance_squared_to(other.center) <= other.radius ** 2
        raise TypeError('Can check center inside of only Sphere for now')

    def collide_with(self, other: 'Sphere'):
            # pushout
            dist = self.center.distance_to(other.center)
            overlap = -(dist - self.radius - other.radius) * 0.5
            self.center += overlap * (self.center - other.center).normalize() * 1.003
            other.center -= overlap * (self.center - other.center).normalize() * 1.003

            # elastic collision
            n = (other.center - self.center).normalize()
            k = self.velocity - other.velocity
            p = 2 * (n * k) / (self.mass + other.mass)
            self.velocity -= p * other.mass * n
            other.velocity += p * self.mass * n

    def update(self):
        self.center += self.velocity
        self.velocity *= self.damping_factor

class RotatorSphere(Sphere):
    def __init__(self, center, radius):
        super().__init__(center, Vector2(0,0), radius, (51, 51, 51))
        self.middle_sphere = Sphere(center, Vector2(0, 0), radius/20, (100, 100, 100))

class PlayerSphere(Sphere):
    max_dodge_duration = 30
    cooldown_duration = 30
    dodge_speed = 1.5
    path_size_per_trail_sphere=10
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.rotating_around : Optional[RotatorSphere] = None
        self.dodge_initiated = False
        self.frames_from_dodge = 0
        self.path : deque[Vector2] = deque(maxlen=self.path_size_per_trail_sphere)
        self.path.append(center)
        self.trail : list[Sphere] = []
        self.queue_to_trail : list[Sphere] = []
        self.alive = True

    def is_dodging(self):
        return 0 < self.frames_from_dodge <= self.max_dodge_duration
    def is_dodge_cooldown(self):
        return self.max_dodge_duration < self.frames_from_dodge < self.max_dodge_duration + self.cooldown_duration
    def can_dodge(self):
        return self.frames_from_dodge == 0

    def add_sphere_to_queue(self, sphere: Sphere):
        self.queue_to_trail.append(sphere)
        self.path = deque(self.path, maxlen=(len(self.trail)+len(self.queue_to_trail)+1) * self.path_size_per_trail_sphere) # type: ignore

    def add_sphere_to_trail(self, sphere: Sphere):
        self.trail.append(sphere)
        sphere.color = self.color

    def remove_sphere(self):
        sphere = self.trail.pop(0)
        self.path = deque(self.path, maxlen=(len(self.trail)+1) * self.path_size_per_trail_sphere) # type: ignore
        return sphere

    def get_sphere_position(self, i) -> Vector2:
        try:
            return self.path[self.path_size_per_trail_sphere * i - 1]
        except IndexError:
            return self.path[-1]

    def update(self):
        if not self.alive: return
        if self.rotating_around is None:
            if self.dodge_initiated:
                self.frames_from_dodge = 1
                self.dodge_initiated = False
            if self.is_dodging():
                self.center += self.velocity * self.dodge_speed
                self.frames_from_dodge += 1
            elif self.is_dodge_cooldown():
                self.frames_from_dodge += 1
                self.center += self.velocity
            else:
                self.frames_from_dodge = 0
                self.center += self.velocity
        else:
            me_rotator_vector = self.rotating_around.center - self.center
            angle = me_rotator_vector.angle_to(self.velocity)
            delta_angle = 360 * DEFAULT_SPEED / (2 * math.pi * me_rotator_vector.magnitude())
            # old_angle = angle
            while angle > 180: angle -= 360
            while angle < -180: angle += 360
            # print(old_angle, angle)
            if angle < 0:
                velocity_rotate_angle = 90
            else:
                delta_angle *= -1
                velocity_rotate_angle = -90
            rotator_me_vector = -me_rotator_vector
            new_rotator_me_vector = rotator_me_vector.rotate(delta_angle)
            self.center = self.rotating_around.center + new_rotator_me_vector
            self.velocity = new_rotator_me_vector.rotate(velocity_rotate_angle)
            self.velocity.scale_to_length(DEFAULT_SPEED)
            # super().update(debug_surface)
        for i, sphere in enumerate(self.trail, 1):
            sphere.center = sphere.center.move_towards(self.get_sphere_position(i), DEFAULT_SPEED*3)
        for i, sphere in enumerate(self.queue_to_trail, len(self.trail)):
            sphere.center = sphere.center.move_towards(self.get_sphere_position(i), DEFAULT_SPEED*3)
            if sphere.center == self.get_sphere_position(i):
                self.add_sphere_to_trail(sphere)
                self.queue_to_trail.remove(sphere)
        self.path.appendleft(Vector2(self.center))

    def draw_debug(self, debug_surface: pygame.Surface):
        size = debug_surface.get_rect().size
        def mul(point, size):
            return point[0]*min(size), point[1]*min(size)
        pygame.draw.line(debug_surface, (255,255,255), mul(self.center, size), mul(self.center+self.velocity*20, size), width=3)
        pygame.draw.circle(debug_surface, (255, 255, 255), mul(self.path[0], size), 5)
        pygame.draw.circle(debug_surface, (255, 255, 255), mul(self.path[-1], size), 5)
        pygame.draw.circle(debug_surface, (0, 0, 0), mul(self.path[-1], size), 3)
        if self.rotating_around:
            pygame.draw.line(debug_surface, (255,0,0), mul(self.center, size), mul(self.rotating_around.center, size), width=3)
            me_rotator_vector = self.rotating_around.center - self.center
            angle = me_rotator_vector.angle_to(self.velocity)
            delta_angle = 360 * DEFAULT_SPEED / (2 * math.pi * me_rotator_vector.magnitude())
            while angle > 180: angle -= 360
            while angle < -180: angle += 360
            if angle < 0:
                velocity_rotate_angle = -90
            else:
                delta_angle *= -1
                velocity_rotate_angle = 90
            rotator_me_vector = -me_rotator_vector
            new_rotator_me_vector = rotator_me_vector.rotate(delta_angle)
            pygame.draw.line(debug_surface, (255,255,0), mul(self.rotating_around.center + new_rotator_me_vector, size), mul(self.rotating_around.center, size), width=3)

class BotState(Enum):
    WAITING = auto()
    GOING_FOR_ROTATOR = auto()
    ROTATING = auto()
    GOING_FOR_SPHERE = auto()

class BotPlayerSphere(PlayerSphere):
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.last_state = None
        self.botstate = BotState.WAITING
        self.wait_time = 5
        self.timer = 0
        self.prev_spheres = 0
        self.font = pygame.freetype.SysFont('arial', 25)

    def calc_first_rotator_hit(self, rotators):
        ray = self.get_ray()
        closest_rotator = None
        closest_distance = 10
        for rotator in rotators:
            distance = ray.intersects_sphere(rotator)
            if distance is not None and distance < closest_distance:
                closest_rotator = rotator
                closest_distance = distance
        return closest_rotator, closest_distance

    def is_in_rotator(self, rotators):
        for rotator in rotators:
            if self.check_center_inside(rotator):
                return True
        return False

    def calc_closest_sphere(self, spheres: list[Sphere]):
        if self.rotating_around:
            spheres = filter(lambda x: self.center.distance_squared_to(self.rotating_around.center) < x.center.distance_squared_to(self.rotating_around.center), spheres)
        return min(spheres, key=lambda x:self.center.distance_squared_to(x.center))

    def get_action(self, state: 'GameState', time_delta: float):
        if not self.alive: return False
        self.last_state = state

        # dodge first
        spheres_to_check = []
        for player_sphere, attacking_spheres in zip(state.player_spheres, state.attacking_spheres):
            if player_sphere is self: continue
            spheres_to_check.extend(player_sphere.trail)
            for sphere in attacking_spheres:
                time = sphere.will_hit_sphere(self)
                if time is not None:
                    print(time)
                if time is not None and time < 10:
                    print(Team(self.color).name, 'jumping to dodge attack', time)
                    return True
            for sphere in spheres_to_check:
                time = self.will_hit_sphere(sphere)
                if time is not None and time < 10:
                    print(Team(self.color).name, 'jumping to dodge trail', time)
                    return True

        # try to attack
        if not self.is_in_rotator(state.rotators):
            if len(self.trail) > 0:
                attacking_sphere = Sphere(self.trail[0].center, self.velocity * 2, SPHERE_SIZE)
                for player in state.player_spheres:
                    if player is self: continue
                    if attacking_sphere.will_hit_sphere(player) is not None:
                        print(Team(self.color).name, 'jumping to attack')
                        return True

        if self.botstate == BotState.WAITING:
            if self.timer < self.wait_time:
                # print('waiting for 5 secs:', state.timer)
                self.timer += time_delta
                return False # do not do anything for 5 seconds
            else:
                print(Team(self.color).name, 'waiting ended')
                self.botstate = BotState.GOING_FOR_ROTATOR
        elif self.botstate == BotState.GOING_FOR_ROTATOR:
            if self.rotating_around:
                self.botstate = BotState.GOING_FOR_SPHERE
                self.timer = 0
                print(Team(self.color).name, 'going for rotator success')
                return False
            if self.is_in_rotator(state.rotators) and self.rotating_around is None:
                print(Team(self.color).name, 'going for rotator try')
                # self.botstate = BotState.GOING_FOR_SPHERE
                # self.timer = 0
                return True
        elif self.botstate == BotState.GOING_FOR_SPHERE:
            if self.timer > 10:
                self.botstate = BotState.GOING_FOR_ROTATOR
                self.timer = 0
                print(Team(self.color).name, 'going for sphere for too long')
                return True # rotating for too long
            self.timer += time_delta
            if len(self.trail) > self.prev_spheres:
                self.botstate = BotState.GOING_FOR_ROTATOR
                self.prev_spheres = len(self.trail)
                print(Team(self.color).name, 'caught a sphere probably')
                return False
            # going for a sphere
            sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
            ray = self.get_ray()
            distance = ray.intersects_sphere(sphere)
            if distance is not None:
                if self.rotating_around is not None:
                    print(Team(self.color).name, 'trying to hit closest sphere from a rotator')
                    return True
                else:
                    # print('trying to hit closest sphere going straight for it')
                    return False
        self.timer += time_delta
        return False

    def draw_debug(self, debug_surface: Surface):
        super().draw_debug(debug_surface)
        size = debug_surface.get_rect().size
        def mul(point):
            return point[0]*min(size), point[1]*min(size)
        state = self.last_state
        if state is None: return
        # rotator, distance = self.calc_first_rotator_hit(self.last_state.rotators)
        # if rotator is not None:
        #     pygame.draw.line(debug_surface, (255,255,255), mul(self.center), mul(rotator.center))
        self.font.render_to(debug_surface, mul(self.center), f'{self.botstate.name} {self.timer:.1f}', self.color, size=10)
        sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
        pygame.draw.circle(debug_surface, self.color, mul(sphere.center), SPHERE_SIZE*min(size)/2)
        ray = self.get_ray()
        distance = ray.intersects_sphere(sphere)
        if distance is not None:
            pygame.draw.line(debug_surface, self.color, mul(self.center), mul(sphere.center))
            # print(f'{ray}, {sphere}')


@dataclass
class Map:
    rotators_coords: list[tuple[float, float, float]]
map1 = Map([
    (0.1, 0.2, ROTATOR_SIZE),
    (0.3666, 0.2, ROTATOR_SIZE),
    (0.6333, 0.2, ROTATOR_SIZE),
    (0.9, 0.2, ROTATOR_SIZE),
    (0.2333, 0.5, ROTATOR_SIZE),
    (0.5, 0.5, ROTATOR_SIZE),
    (0.7666, 0.5, ROTATOR_SIZE),
    (0.1, 0.8, ROTATOR_SIZE),
    (0.3666, 0.8, ROTATOR_SIZE),
    (0.6333, 0.8, ROTATOR_SIZE),
    (0.9, 0.8, ROTATOR_SIZE),
])

class GameStage(Enum):
    ROTATING_AROUND_CENTER = 1
    GAMING = 2
    SHOWING_RESULTS = 3
    RESTART_ROUND = 4
    END_SCREEN = 5

class Bot(Enum):
    IS_BOT_1 = auto()
    IS_BOT_2 = auto()
    IS_BOT_3 = auto()
    IS_BOT_4 = auto()
    IS_BOT_5 = auto()
    IS_BOT_6 = auto()
    IS_BOT_7 = auto()
    IS_BOT_8 = auto()
    IS_BOT_9 = auto()
    IS_BOT_10 = auto()
    IS_BOT_11 = auto()
    IS_BOT_12 = auto()

@dataclass
class PlayerScore:
    old_score: int = -1
    old_position: int = -1
    new_score: int = -1
    new_position: int = -1
    color: Optional[tuple[int,int,int]] = None

@dataclass
class GameState:
    player_spheres: list[PlayerSphere]
    active_spheres: list[Sphere]
    inactive_spheres: list[Sphere]
    attacking_spheres: list[list[Sphere]]
    rotators: list[RotatorSphere]
    timer: float
    death_order: list[int]
    random: random.Random
    def update_to_front(self, player_scores: list[PlayerScore], how_to_win_text: str, stage: GameStage, someone_won: Optional[tuple[int, int, int]]):
        return GameStateFront(self.player_spheres, self.active_spheres, self.inactive_spheres, self.attacking_spheres, self.rotators, self.timer, self.death_order, self.random,
                              player_scores, how_to_win_text, stage, someone_won)

@dataclass
class GameStateFront(GameState):
    player_scores: list[PlayerScore]
    how_to_win_text: str
    stage: GameStage
    someone_won: Optional[tuple[int, int, int]]

class Game:
    def __init__(self, colors: dict[int, tuple[Team, str]], seed=None) -> None:
        size = (2, 1)
        self.size = size
        self.leftwall = None
        self.rightwall = None
        self.topwall = None
        self.bottomwall = None
        self.debug_surface = None
        self.set_dimensions(size) # set these things

        self.colors = colors
        self.num_players = 0
        self.keys_list = []
        self.actions_in_last_frame: list[int] = []
        self.register_players_and_keys(list(self.colors.keys())) # set things above
        self.old_scores = []
        self.scores = [0] * self.num_players

        self.rotators = []
        self.load_map(map1)

        self.seed = seed
        self.random = None

        self.player_spheres: list[PlayerSphere] = []
        self.bot_player_spheres: list[BotPlayerSphere] = []
        self.active_spheres: list[Sphere] = []
        self.inactive_spheres: list[Sphere] = []
        self.attacking_spheres: list[list[Sphere]] = None
        self.someone_won = False

        self.stage = GameStage.ROTATING_AROUND_CENTER
        # ROTATING_AROUND_CENTER
        self.timer = 0
        self.starting_angle = 0

        # GAMING
        self.death_order: list[int] = []

        # SHOWING_RESULTS
        self.score1 = 0
        self.score2 = 0
        self.how_to_win_text = ''
        self.player_scores = None

        self.restart_round(seed)


    def load_map(self, map_: Map):
        for i in map_.rotators_coords:
            self.rotators.append(RotatorSphere(Vector2(i[0]*self.size[0], i[1]*self.size[1]), i[2]))

    def restart_round(self, seed=None):
        self.seed = seed
        if self.seed is None:
            self.seed = random.randint(0, 1000000000)
        self.random = random.Random(self.seed)

        self.starting_angle = self.random.uniform(0, 360)

        self.bot_player_spheres = []
        self.player_spheres = []
        for key, (team, name) in self.colors.items():
            vel = Vector2()
            vel.from_polar((DEFAULT_SPEED, self.random.randint(0, 360)))
            if key in list(Bot):
                ps = BotPlayerSphere(Vector2(0, 0), vel, PLAYER_SIZE, team.value)
                self.bot_player_spheres.append(ps)
            else:
                ps = PlayerSphere(Vector2(0, 0), vel, PLAYER_SIZE, team.value)
            self.player_spheres.append(ps)
        self.attacking_spheres = [[] for _ in range(self.num_players)]

        self.inactive_spheres = []
        self.active_spheres = []
        for i in range(10):
            self.add_random_sphere()

        self.someone_won = False

        self.stage = GameStage.ROTATING_AROUND_CENTER
        self.timer = 0
        self.death_order: list[int] = []

    def restart_game(self):
        self.scores = [0] * self.num_players
        self.restart_round()

    def set_dimensions(self, size):
        self.size = size
        self.leftwall = VerticalLine(0)
        self.rightwall = VerticalLine(size[0])
        self.topwall = HorizontalLine(0)
        self.bottomwall = HorizontalLine(size[1])

        self.debug_surface = pygame.Surface(self.size)
        # self.debug_surface.fill(pygame.Color('#00000000'))

    def register_players_and_keys(self, keys_list: list):
        self.num_players = len(keys_list)
        self.keys_list = keys_list
        self.actions_in_last_frame = []

    def get_random_spawn_position(self, radius):
        return (self.random.uniform(radius, self.size[0]-radius),
                self.random.uniform(radius, self.size[1]-radius))

    def add_random_sphere(self):
        self.active_spheres.append(Sphere(Vector2(self.get_random_spawn_position(SPHERE_SIZE)),
                                   Vector2(0, 0),
                                   SPHERE_SIZE,
                                   (255,255,255)))

    def check_wall_collision(self, sphere: Sphere):
        if sphere.intersects(self.topwall):
            sphere.velocity.y *= -1
            return True
        if sphere.intersects(self.bottomwall):
            sphere.velocity.y *= -1
            return True
        if sphere.intersects(self.leftwall):
            sphere.velocity.x *= -1
            return True
        if sphere.intersects(self.rightwall):
            sphere.velocity.x *= -1
            return True

    def process_actions(self, actions):
        # self.actions_in_last_frame: list[int] = []
        for action in actions:
            if action in self.keys_list:
                self.actions_in_last_frame.append(self.keys_list.index(action))
        # if len(actions) > 0:
        #     print(actions, self.actions_in_last_frame)

    def perform_actions(self):
        if self.actions_in_last_frame is not None:
            for player in self.actions_in_last_frame:
                player_sphere = self.player_spheres[player]
                for rotator in self.rotators:
                    if player_sphere.check_center_inside(rotator) and not player_sphere.is_dodging():
                        if player_sphere.rotating_around is None:
                            player_sphere.rotating_around = rotator
                        else:
                            player_sphere.rotating_around = None
                        break
                else:
                    # not in a rotator
                    if player_sphere.can_dodge():
                        player_sphere.dodge_initiated = True
                        if len(player_sphere.trail) > 0:
                            attacking_sphere = player_sphere.remove_sphere()
                            attacking_sphere.velocity = player_sphere.velocity * 2
                            attacking_sphere.damping_factor = 1
                            self.attacking_spheres[player].append(attacking_sphere)
                if self.stage == GameStage.END_SCREEN:
                    self.timer += 2
        self.actions_in_last_frame = []

    def update_positions_and_wall_collisions(self):
        for i in self.player_spheres:
            if not i.alive: continue
            if self.check_wall_collision(i):
                i.rotating_around = None
            i.update()
        for player, attacking_spheres in zip(self.player_spheres, self.attacking_spheres):
            for i in attacking_spheres:
                if self.check_wall_collision(i) and not player.is_dodging():
                    i.color = (255, 255, 255)
                    self.inactive_spheres.append(i)
                    attacking_spheres.remove(i)
                    i.damping_factor = 0.98
                i.update()
        for i in self.active_spheres:
            self.check_wall_collision(i)
            i.update()
        for i in self.inactive_spheres:
            self.check_wall_collision(i)
            i.update()

    def update_positions_to_rotate_around_center(self):
        ROTATION_SPEED = 500
        FINAL_SIZE = 0.15
        t = self.timer / 3
        center = Vector2(self.size) / 2
        right = Vector2(FINAL_SIZE, 0)
        for index, sphere in enumerate(self.player_spheres):
            angle = index / self.num_players * 360 + t * ROTATION_SPEED + self.starting_angle
            direction = right.rotate(angle)
            position = center.lerp(center+direction, t)
            sphere.center = position
            if t > 0.5:
                velocity = (center - position).rotate(-90)
                velocity.scale_to_length(DEFAULT_SPEED)
                sphere.velocity = velocity

    def process_collisions(self):
        for index, sphere in enumerate(self.player_spheres):
            if not sphere.alive: continue
            # other players
            for sphere_to_check in self.player_spheres[index+1:]:
                if not sphere_to_check.alive: continue
                if sphere.intersects(sphere_to_check):
                    sphere.rotating_around = None
                    sphere_to_check.rotating_around = None
                    if not sphere.is_dodging() and not sphere_to_check.is_dodging():
                        sphere.collide_with(sphere_to_check)

            # other players' trails
            for other_player in self.player_spheres:
                if sphere == other_player:
                    continue
                for sphere_to_check in other_player.trail:
                    if sphere.intersects(sphere_to_check) and not sphere.is_dodging():
                        self.process_player_death(index, sphere, killer_sphere=other_player)

            # attacking spheres
            for index2, players_spheres in enumerate(self.attacking_spheres):
                if index == index2: continue # this players' spheres
                for sphere_to_check in players_spheres:
                    if sphere.intersects(sphere_to_check) and not sphere.is_dodging():
                        self.process_player_death(index, sphere, killer_index=index2)

            # white spheres
            for sphere_to_check in self.active_spheres:
                if sphere.intersects(sphere_to_check):
                    if not sphere.is_dodging():
                        sphere.add_sphere_to_queue(sphere_to_check)
                        self.active_spheres.remove(sphere_to_check)
                        self.add_random_sphere()
            for sphere_to_check in self.inactive_spheres:
                if sphere.intersects(sphere_to_check):
                    if not sphere.is_dodging():
                        sphere.add_sphere_to_queue(sphere_to_check)
                        self.inactive_spheres.remove(sphere_to_check)

    def process_player_death(self, killed_index: int, killed_sphere: PlayerSphere, *, killer_index: Optional[int] = None, killer_sphere: Optional[PlayerSphere] = None):
        if killer_index is None and killer_sphere is None:
            raise ValueError('provide at least one')
        if killer_sphere is None:
            killer_sphere = self.player_spheres[killer_index]
        if not killed_sphere.alive: return
        self.death_order.append(killed_index)
        for sphere_to_pop in killed_sphere.trail:
            killer_sphere.add_sphere_to_queue(sphere_to_pop)
        killed_sphere.trail = []
        killed_sphere.alive = False

    def process_results(self, winner_index):
        assert len(self.death_order) == self.num_players-1, len(self.death_order)
        assert winner_index not in self.death_order
        self.death_order.append(winner_index)

        self.old_scores = self.scores.copy()
        for score, player in enumerate(self.death_order):
            self.scores[player] += score
        self.score1, self.score2 = heapq.nlargest(2, self.scores)
        self.death_order = []

        player_scores = [PlayerScore(color=player.color) for player in self.player_spheres]

        sorted_old_scores = sorted(enumerate(self.old_scores), key=lambda x:x[1], reverse=True)
        for i, (player_index, old_score) in enumerate(sorted_old_scores):
            player_scores[player_index].old_position = i
            player_scores[player_index].old_score = old_score

        sorted_scores = sorted(enumerate(self.scores), key=lambda x:x[1], reverse=True)
        for i, (player_index, score) in enumerate(sorted_scores):
            player_scores[player_index].new_position = i
            player_scores[player_index].new_score = score
        self.player_scores = player_scores


    def update(self, time_delta: float):
        # get bots actions
        state = self.get_state()
        bots_actions = []
        for bot, key in zip(self.bot_player_spheres, Bot):
            action = bot.get_action(state, time_delta)
            if action:
                print(f'{Team(bot.color).name} action at {self.timer:.1f}')
                # print(f'{self.bot_player_spheres}')
                bots_actions.append(key)
        self.process_actions(bots_actions)

        # perform actions. actions were commited in process actions function
        if self.stage == GameStage.ROTATING_AROUND_CENTER:
            if self.timer < 3:
                self.update_positions_to_rotate_around_center()
                self.timer += time_delta
            else:
                self.stage = GameStage.GAMING
                self.timer = 0
        elif self.stage == GameStage.GAMING:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)

            self.timer += time_delta

            winner = [(index, p.color) for index, p in enumerate(self.player_spheres) if p.alive]
            if len(winner) == 1 and self.num_players > 1:
                self.stage = GameStage.SHOWING_RESULTS
                self.timer = 0
                self.process_results(winner[0][0])

                if self.score1 < 5 * (self.num_players-1):
                    self.how_to_win_text = f'Reach {5 * (self.num_players-1)} points'
                    self.next_stage = GameStage.RESTART_ROUND
                elif self.score1 >= 5 * (self.num_players-1) and self.score1 - self.score2 < 2:
                    self.how_to_win_text = 'Get a 2-point lead'
                    self.next_stage = GameStage.RESTART_ROUND
                else:
                    self.someone_won = winner[0][1]
                    self.next_stage = GameStage.END_SCREEN
        elif self.stage == GameStage.SHOWING_RESULTS:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)

            if self.timer > 5:
                self.stage = self.next_stage
                self.timer = 0
            self.timer += time_delta
        elif self.stage == GameStage.RESTART_ROUND:
            self.restart_round()
        elif self.stage == GameStage.END_SCREEN:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)
            if self.timer > 30:
                self.restart_game()
            self.timer += time_delta


    def get_state(self):
        return GameState(self.player_spheres,
                         self.active_spheres,
                         self.inactive_spheres,
                         self.attacking_spheres,
                         self.rotators,
                         self.timer,
                         self.death_order,
                         self.random)

    def get_front_state(self):
        return self.get_state().update_to_front(self.player_scores, self.how_to_win_text, self.stage, self.someone_won)


    def set_state(self, state: GameState):
        self.rotators = state.rotators
        self.player_spheres = state.player_spheres
        self.active_spheres = state.active_spheres
        self.inactive_spheres = state.inactive_spheres
        self.attacking_spheres = state.attacking_spheres
        self.timer = state.timer
        self.death_order = state.death_order
        self.random = state.random
        # self.stage = state.stage

    def draw_debug(self, debug_surface: pygame.Surface):
        for i in self.player_spheres:
            i.draw_debug(debug_surface)
