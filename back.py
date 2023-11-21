from dataclasses import dataclass
from enum import Enum
from typing import Union
import math

import pygame
from pygame import Vector2

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

    def collide_with(self, other: 'Sphere'):
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

class Game:
    def __init__(self, size) -> None:
        self.set_dimensions(size)
        self.rotator = RotatorSphere(Vector2(300, 150), 150)
        self.s1 = Sphere(Vector2(500, 100 + 20 * math.cos(45/180*math.pi)), Vector2(-1, 0), 10, Team.RED.value)
        self.s2 = Sphere(Vector2(100, 100), Vector2(1, 0), 10, Team.BLUE.value)
        self.spheres = [self.s1, self.s2]
        self.rotators = [self.rotator]

    def set_dimensions(self, size):
        self.size = size
        self.leftwall = VerticalLine(0)
        self.rightwall = VerticalLine(size[0])
        self.topwall = HorizontalLine(0)
        self.bottomwall = HorizontalLine(size[1])

    def update(self, time_delta: float):
        self.s1.update()
        self.s2.update()

        for index, sphere in enumerate(self.spheres, 1):
            if sphere.check_collision(self.topwall):
                sphere.velocity.y *= -1
            if sphere.check_collision(self.bottomwall):
                sphere.velocity.y *= -1
            if sphere.check_collision(self.leftwall):
                sphere.velocity.x *= -1
            if sphere.check_collision(self.rightwall):
                sphere.velocity.x *= -1

            for sphere_to_check in self.spheres[index:]:
                if sphere.check_collision(sphere_to_check):
                    sphere.collide_with(sphere_to_check)
                    sphere.velocity.normalize()

    def get_state(self):
        return {'rotators': self.rotators,
                'spheres': self.spheres,}