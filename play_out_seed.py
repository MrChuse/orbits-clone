from traceback import print_exc

import pygame

from screens import (GameScreen)
from battle_the_bots import colors

def main():
    pygame.init()
    pygame.display.set_caption('Orbits clone')
    settings = {'fullscreen': False,
                'language': 'en'}
    if settings['fullscreen']:
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window_surface = pygame.display.set_mode((600, 300), pygame.RESIZABLE)

    GameScreen(window_surface, colors, seed=649766108).main()

if __name__ == '__main__':
    main()
