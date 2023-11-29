from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, Optional
from collections import deque
import math

import pygame
from pygame import Vector2

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
BURST_SIZE = REFERENCE_BURST_OUTER_SIZE / REFERENCE_SCREEN_SIZE / 2
BURST_INNER_RATIO = REFERENCE_BURST_INNER_SIZE / REFERENCE_BURST_OUTER_SIZE

DEFAULT_SPEED = 2 / 400

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

    def intersects(self, other: 'Sphere'):
        return self.center.distance_squared_to(other.center) <= (self.radius + other.radius) ** 2
    def intersects_vertical_line(self, other: VerticalLine):
            return other.x - self.radius < self.center.x < other.x + self.radius
    def intersects_horizontal_line(self, other: HorizontalLine):
        return other.y - self.radius < self.center.y < other.y + self.radius


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

    def check_center_inside(self, other: 'Sphere'):
        return self.center.distance_squared_to(other.center) <= other.radius ** 2

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

class Burst(Sphere):
    def __init__(self, center, radius):
        super().__init__(center, Vector2(0,0), radius, (255, 255, 255))
        self.middle_sphere = Sphere(center, Vector2(0, 0), radius * BURST_INNER_RATIO, (100, 100, 100))
        self.grow_rate = radius / 5
        self.alive = True
        self.active = False
        self.active_player: Optional[PlayerSphere] = None
        self.frames_from_burst = 0
        self.frames_from_spawn = 0

    def activate(self, active_player):
        self.active = True
        self.active_player = active_player

    def update(self):
        if self.active:
            if self.frames_from_burst < 40:
                self.radius += self.grow_rate
                self.middle_sphere.radius += self.grow_rate
            else:
                self.alive = False
            self.frames_from_burst += 1
        elif self.frames_from_spawn > 1200:
            self.alive = False
        self.frames_from_spawn += 1




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

    def remove_sphere(self, index=0):
        sphere = self.trail.pop(index)
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

@dataclass
class PlayerScore:
    old_score: int = -1
    old_position: int = -1
    new_score: int = -1
    new_position: int = -1
    color: Optional[tuple[int,int,int]] = None

class GameStage(Enum):
    ROTATING_AROUND_CENTER = 1
    GAMING = 2
    SHOWING_RESULTS = 3
    RESTART_ROUND = 4
    END_SCREEN = 5

@dataclass
class GameState:
    player_spheres: list[PlayerSphere]
    active_spheres: list[Sphere]
    inactive_spheres: list[Sphere]
    attacking_spheres: list[list[Sphere]]
    bursts: list[Burst]
    rotators: list[RotatorSphere]
    timer: float
    death_order: list[int]
    def update_to_front(self, player_scores: list[PlayerScore], how_to_win_text: str, stage: GameStage, someone_won: Optional[tuple[int, int, int]]):
        return GameStateFront(self.player_spheres, self.active_spheres, self.inactive_spheres, self.attacking_spheres, self.bursts, self.rotators, self.timer, self.death_order,# self.random_,
                              player_scores, how_to_win_text, stage, someone_won)

@dataclass
class GameStateFront(GameState):
    player_scores: list[PlayerScore]
    how_to_win_text: str
    stage: GameStage
    someone_won: Optional[tuple[int, int, int]]

@dataclass
class Map:
    rotators_coords: list[tuple[float, float, float]]

class BotKeys(Enum):
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
