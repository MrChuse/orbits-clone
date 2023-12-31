from enum import Enum, auto
import logging

import pygame
import pygame.freetype
pygame.freetype.init()
font = pygame.freetype.SysFont('arial', 25)

from back.core import Sphere, GameState, SPHERE_SIZE, Team
from . import Bot

class BotState(Enum):
    WAITING = auto()
    GOING_FOR_ROTATOR = auto()
    ROTATING = auto()
    GOING_FOR_SPHERE = auto()

class DodgingCollectSphereBot(Bot):
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.last_state = None
        self.botstate = BotState.WAITING
        self.wait_time = 5
        self.timer = 0
        self.prev_spheres = 0

    def calc_closest_sphere(self, spheres: list[Sphere]):
        if self.rotating_around:
            spheres = filter(lambda x: self.center.distance_squared_to(self.rotating_around.center) < x.center.distance_squared_to(self.rotating_around.center), spheres)
        return min(spheres, key=lambda x:self.center.distance_squared_to(x.center))

    def get_action(self, state: GameState, time_delta: float):
        if not self.alive: return False
        self.last_state = state

        # dodge first
        spheres_to_check = []
        for player_sphere in state.player_spheres:
            if player_sphere is self: continue
            spheres_to_check.extend(player_sphere.trail)
            for sphere in player_sphere.attacking_spheres:
                time = sphere.will_hit_sphere(self)
                if time is not None and time < 10:
                    # logging.info(Team(self.color).name, 'jumping to dodge attack', time)
                    return True
        for sphere in spheres_to_check:
            time = self.will_hit_sphere(sphere)
            if time is not None and time < 10:
                # logging.info(Team(self.color).name, 'jumping to dodge trail', time)
                return True

        if self.botstate == BotState.WAITING:
            if self.timer < self.wait_time:
                # logging.info('waiting for 5 secs:', state.timer)
                self.timer += time_delta
                return False # do not do anything for 5 seconds
            else:
                # logging.info(Team(self.color).name, 'waiting ended')
                self.botstate = BotState.GOING_FOR_ROTATOR
        elif self.botstate == BotState.GOING_FOR_ROTATOR:
            if self.rotating_around:
                self.botstate = BotState.GOING_FOR_SPHERE
                self.timer = 0
                # logging.info(Team(self.color).name, 'going for rotator success')
                return False
            if self.is_in_rotator(state.rotators) and self.rotating_around is None:
                return True
        elif self.botstate == BotState.GOING_FOR_SPHERE:
            if self.timer > 10:
                self.botstate = BotState.GOING_FOR_ROTATOR
                self.timer = 0
                # logging.info(Team(self.color).name, 'going for sphere for too long')
                return True # rotating for too long
            self.timer += time_delta
            if len(self.trail) > self.prev_spheres:
                self.botstate = BotState.GOING_FOR_ROTATOR
                self.prev_spheres = len(self.trail)
                # logging.info(Team(self.color).name, 'caught a sphere probably')
                return False
            # going for a sphere
            sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
            ray = self.get_ray()
            distance = ray.intersects_sphere(sphere)
            if distance is not None:
                if self.rotating_around is not None:
                    # logging.info(Team(self.color).name, 'trying to hit closest sphere from a rotator')
                    return True
                else:
                    # logging.info('trying to hit closest sphere going straight for it')
                    return False
        self.timer += time_delta
        return False

    def draw_debug(self, debug_surface: pygame.Surface):
        super().draw_debug(debug_surface)
        size = debug_surface.get_rect().size
        def mul(point):
            return point[0]*min(size), point[1]*min(size)
        state = self.last_state
        if state is None: return
        # rotator, distance = self.calc_first_rotator_hit(self.last_state.rotators)
        # if rotator is not None:
        #     pygame.draw.line(debug_surface, (255,255,255), mul(self.center), mul(rotator.center))
        font.render_to(debug_surface, mul(self.center), f'{self.botstate.name} {self.timer:.1f}', self.color, size=10)
        sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
        pygame.draw.circle(debug_surface, self.color, mul(sphere.center), SPHERE_SIZE*min(size)/2)
        ray = self.get_ray()
        distance = ray.intersects_sphere(sphere)
        if distance is not None:
            pygame.draw.line(debug_surface, self.color, mul(self.center), mul(sphere.center))

