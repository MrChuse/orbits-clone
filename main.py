from traceback import print_exc

import pygame

from screens import (GameScreen, PickColorScreen, LocalOnlinePickerScreen,
                    HostPickColorScreen, ClientPickColorScreen,
                    HostGameScreen, ClientGameScreen)

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
    settings = {'fullscreen': True,
                'language': 'en'}
    if settings['fullscreen']:
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window_surface = pygame.display.set_mode((600, 300), pygame.RESIZABLE)

    lop = LocalOnlinePickerScreen(window_surface)
    is_local: str = lop.main() # type: ignore
    if lop.force_quit:
        return
    if is_local == 'local':
        pcs = PickColorScreen(window_surface)
        colors = pcs.main()
        if pcs.force_quit:
            return
        GameScreen(window_surface, colors).main()
    elif is_local.startswith('online'):
        parts = is_local.split()
        if len(parts) == 2 and parts[1] == 'host':
            hpcs = HostPickColorScreen(window_surface)
            result = hpcs.main()
            if hpcs.force_quit:
                return
            colors, server = result
            hgs = HostGameScreen(window_surface, colors, server)
            hgs.main()

        elif len(parts) == 3 and parts[1] == 'client':
            cpcs = ClientPickColorScreen(window_surface, parts[2])
            result = cpcs.main()
            if cpcs.force_quit:
                return
            colors, sock, server = result
            cgs = ClientGameScreen(window_surface, colors, sock, server)
            cgs.main()


if __name__ == '__main__':
    main()
