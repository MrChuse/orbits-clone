import pygame

from back import Sphere, RotatorSphere, PlayerSphere

def draw_sphere(surface: pygame.Surface, sphere: Sphere, force_color=None):
    if force_color is None:
        force_color = sphere.color
    pygame.draw.ellipse(surface, color=force_color, rect=sphere.get_rect())

def draw_rotator_sphere(surface, rotator: RotatorSphere):
    draw_sphere(surface, rotator)
    draw_sphere(surface, rotator.middle_sphere)

def draw_player(surface, sphere: PlayerSphere):
    if not sphere.alive: return
    if sphere.is_dodging():
        pygame.draw.ellipse(surface, color=pygame.Color(255,255,255).lerp(sphere.color, 0.7), rect=sphere.get_rect())
    else:
        pygame.draw.ellipse(surface, color=sphere.color, rect=sphere.get_rect())
    for i in sphere.trail:
        draw_sphere(surface, i)
    for i in sphere.queue_to_trail:
        draw_sphere(surface, i)

def draw_game(surface, state):
    for i in state['rotators']:
        draw_rotator_sphere(surface, i)
    for i in state['spheres']:
        draw_sphere(surface, i)
    for players_spheres in state['attacking_spheres']:
        for i in players_spheres:
            draw_sphere(surface, i)
    for i in state['players']:
        draw_player(surface, i)