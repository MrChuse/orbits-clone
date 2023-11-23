from traceback import print_exc

import pygame

from screen import GameScreen, PickColorScreen

# from config import load_settings
# from forestry import NotEnoughResourcesError
# from ui.custom_events import APPLY_VOLUME_CHANGE
# keep TutorialStage here because needed for backwards compatibility with pickle.load
# from ui.game_components import GUI, TutorialStage

# trash slot for inventory
# controls for apiary and inventory


def main():
    pygame.init()
    pygame.display.set_caption('Orbits clone')
    settings = {'fullscreen': False,
                'language': 'en'}
    if settings['fullscreen']:
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window_surface = pygame.display.set_mode((800, 500), pygame.RESIZABLE)

    colors = PickColorScreen(window_surface).main()
    GameScreen(window_surface, colors).main()


if __name__ == '__main__':
    main()
