from back.core import GameState, Sphere, SPHERE_SIZE
from . import Bot

import pygame
import pygame.freetype
pygame.freetype.init()
font = pygame.freetype.SysFont('arial', 25)

class CollectSphereBot(Bot):
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.timer = 0

    def calc_closest_sphere(self, spheres: list[Sphere]):
        return min(spheres, key=lambda x:self.center.distance_squared_to(x.center))

    def get_action(self, state: GameState, time_delta: float) -> bool:
        self.last_state = state
        # wait
        if self.timer < 5:
            self.timer += time_delta
            return False

        # cling to any rotator
        if not self.rotating_around and self.is_in_rotator(state.rotators):
            return True

        # rotating now
        # calculate closest sphere and go for it
        closest_sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
        if self.get_ray().intersects_sphere(closest_sphere):
            return True # uncling

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
        # font.render_to(debug_surface, mul(self.center), f'{self.botstate.name} {self.timer:.1f}', self.color, size=10)
        sphere = self.calc_closest_sphere(state.active_spheres+state.inactive_spheres)
        pygame.draw.circle(debug_surface, self.color, mul(sphere.center), SPHERE_SIZE*min(size)/2)
        ray = self.get_ray()
        distance = ray.intersects_sphere(sphere)
        if distance is not None:
            pygame.draw.line(debug_surface, self.color, mul(self.center), mul(sphere.center))
            # print(f'{ray}, {sphere}')