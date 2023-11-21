import pygame

from back import Sphere, RotatorSphere

def draw_sphere(surface: pygame.Surface, sphere: Sphere):
    pygame.draw.ellipse(surface, color=sphere.color, rect=sphere.get_rect())

def draw_rotator_sphere(surface, rotator: RotatorSphere):
    draw_sphere(surface, rotator)
    draw_sphere(surface, rotator.middle_sphere)

def draw_game(surface, state):
    for i in state['rotators']:
        draw_rotator_sphere(surface, i)
    for i in state['spheres']:
        draw_sphere(surface, i)