import pygame

from back import Sphere, RotatorSphere, PlayerSphere

def draw_sphere(surface: pygame.Surface, sphere: Sphere, game_size: tuple[int, int], force_color=None):
    if force_color is None:
        force_color = sphere.color
    rect = sphere.get_rect()
    new_rect = tuple(map(lambda i : i * min(game_size), rect))
    pygame.draw.ellipse(surface, color=force_color, rect=new_rect)

def draw_rotator_sphere(surface, rotator: RotatorSphere, game_size):
    draw_sphere(surface, rotator, game_size)
    draw_sphere(surface, rotator.middle_sphere, game_size)

def draw_player(surface, sphere: PlayerSphere, game_size):
    if not sphere.alive: return
    if sphere.is_dodging():
        draw_sphere(surface, sphere, game_size, force_color=pygame.Color(255,255,255).lerp(sphere.color, 0.7))
    else:
        draw_sphere(surface, sphere, game_size)
    for i in sphere.trail:
        draw_sphere(surface, i, game_size)
    for i in sphere.queue_to_trail:
        draw_sphere(surface, i, game_size)

def draw_game(surface, state, game_size):
    for i in state['rotators']:
        draw_rotator_sphere(surface, i, game_size)
    for i in state['spheres']:
        draw_sphere(surface, i, game_size)
    for players_spheres in state['attacking_spheres']:
        for i in players_spheres:
            draw_sphere(surface, i, game_size)
    for i in state['players']:
        draw_player(surface, i, game_size)