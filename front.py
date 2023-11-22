import pygame

from back import Sphere, RotatorSphere, PlayerSphere

def draw_sphere(surface: pygame.Surface, sphere: Sphere):
    pygame.draw.ellipse(surface, color=sphere.color, rect=sphere.get_rect())

def draw_rotator_sphere(surface, rotator: RotatorSphere):
    draw_sphere(surface, rotator)
    draw_sphere(surface, rotator.middle_sphere)

def draw_player(surface, sphere: PlayerSphere):
    if sphere.is_dodging():
        pygame.draw.ellipse(surface, color=pygame.Color(255,255,255).lerp(sphere.color, 0.7), rect=sphere.get_rect())
    else:
        pygame.draw.ellipse(surface, color=sphere.color, rect=sphere.get_rect())

def draw_game(surface, state):
    for i in state['rotators']:
        draw_rotator_sphere(surface, i)
    for i in state['players']:
        draw_player(surface, i)