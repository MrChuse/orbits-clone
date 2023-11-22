from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union
import math

import pygame
from pygame import Vector2

DEFAULT_SPEED = 2
PLAYER_SIZE = 10

class Team(Enum):
    RED = (255, 40, 40)
    BLUE = (40, 40, 255)

@dataclass
class VerticalLine:
    x: float
@dataclass
class HorizontalLine:
    y: float


@dataclass
class Sphere:
    center: Vector2
    velocity: Vector2
    radius: float
    color: tuple[int, int, int]
    mass : float = 1

    def get_rect(self):
        return self.center.x-self.radius, self.center.y-self.radius, self.radius*2, self.radius*2

    def check_collision(self, other: Union['Sphere', VerticalLine, HorizontalLine]):
        if isinstance(other, Sphere):
            return self.center.distance_squared_to(other.center) <= (self.radius + other.radius) ** 2
        if isinstance(other, VerticalLine):
            return other.x - self.radius < self.center.x < other.x + self.radius
        if isinstance(other, HorizontalLine):
            return other.y - self.radius < self.center.y < other.y + self.radius
        raise TypeError('Can check collisions only with Sphere, VerticalLine and HorizontalLine for now')

    def check_center_inside(self, other: 'Sphere'):
        if isinstance(other, Sphere):
            return self.center.distance_squared_to(other.center) <= other.radius ** 2
        raise TypeError('Can check center inside of only Sphere for now')

    def collide_with(self, other: 'Sphere'):
            # pushout
            dist = self.center.distance_to(other.center)
            overlap = -(dist - self.radius - other.radius) * 0.5
            self.center += overlap * (self.center - other.center).normalize()
            other.center -= overlap * (self.center - other.center).normalize()

            # elastic collision
            n = (other.center - self.center).normalize()
            k = self.velocity - other.velocity
            p = 2 * (n * k) / (self.mass + other.mass)
            self.velocity -= p * other.mass * n
            other.velocity += p * self.mass * n

    def update(self):
        self.center += self.velocity

class RotatorSphere(Sphere):
    def __init__(self, center, radius):
        super().__init__(center, Vector2(0,0), radius, (51, 51, 51))
        self.middle_sphere = Sphere(center, Vector2(0, 0), radius/20, (100, 100, 100))

class PlayerSphere(Sphere):
    max_dodge_duration = 30
    cooldown_duration = 30
    dodge_speed = 1.5
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.rotating_around : Optional[RotatorSphere] = None
        self.dodge_initiated = False
        self.frames_from_dodge = 0

    def is_dodging(self):
        return 0 < self.frames_from_dodge <= self.max_dodge_duration
    def is_dodge_cooldown(self):
        return self.max_dodge_duration < self.frames_from_dodge < self.max_dodge_duration + self.cooldown_duration
    def can_dodge(self):
        return self.frames_from_dodge == 0

    def update(self):
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
            return

    def draw_debug(self, debug_surface: pygame.Surface):
        pygame.draw.line(debug_surface, (255,255,255), self.center, self.center+self.velocity*20, width=3)
        if self.rotating_around:
            pygame.draw.line(debug_surface, (255,0,0), self.center, self.rotating_around.center, width=3)
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
            pygame.draw.line(debug_surface, (255,255,0), self.rotating_around.center + new_rotator_me_vector, self.rotating_around.center, width=3)


class Game:
    def __init__(self, size) -> None:
        self.set_dimensions(size)
        self.rotator = RotatorSphere(Vector2(300, 150), 150)
        self.s1 = PlayerSphere(Vector2(500, 100 + 20 * math.cos(45/180*math.pi)), Vector2(-DEFAULT_SPEED, 0), PLAYER_SIZE, Team.RED.value)
        self.s2 = PlayerSphere(Vector2(100, 200), Vector2(DEFAULT_SPEED, 0), PLAYER_SIZE, Team.BLUE.value)
        self.player_spheres: list[PlayerSphere] = [self.s1, self.s2]
        self.spheres = []
        self.rotators = [self.rotator]

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

    def process_actions(self, actions):
        self.actions_in_last_frame: list[int] = []
        for action in actions:
            if action in self.keys_list:
                self.actions_in_last_frame.append(self.keys_list.index(action))

    def update(self, time_delta: float):
        # self.debug_surface.fill(pygame.Color('#00000000'))
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
                    if player_sphere.can_dodge():
                        player_sphere.dodge_initiated = True


        self.s1.update()
        self.s2.update()

        for index, sphere in enumerate(self.player_spheres, 1):
            if sphere.check_collision(self.topwall):
                sphere.velocity.y *= -1
                sphere.rotating_around = None
            if sphere.check_collision(self.bottomwall):
                sphere.velocity.y *= -1
                sphere.rotating_around = None
            if sphere.check_collision(self.leftwall):
                sphere.velocity.x *= -1
                sphere.rotating_around = None
            if sphere.check_collision(self.rightwall):
                sphere.velocity.x *= -1
                sphere.rotating_around = None

            for sphere_to_check in self.player_spheres[index:]:
                if sphere.check_collision(sphere_to_check):
                    sphere.rotating_around = None
                    sphere_to_check.rotating_around = None
                    if not sphere.is_dodging() and not sphere_to_check.is_dodging():
                        sphere.collide_with(sphere_to_check)
        for i in self.player_spheres:
            i.velocity.scale_to_length(DEFAULT_SPEED)
        return self.debug_surface

    def get_state(self):
        return {'rotators': self.rotators,
                'players': self.player_spheres,
                'spheres': self.spheres,}

    def draw_debug(self, debug_surface: pygame.Surface):
        self.s1.draw_debug(debug_surface)
        self.s2.draw_debug(debug_surface)