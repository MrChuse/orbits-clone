from traceback import print_exc

import pygame

import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(name)-8s %(filename)s:%(lineno)s %(message)s')

from screens import (GameScreen, PickColorScreen, LocalOnlinePickerScreen,
                    HostPickColorScreen, ClientPickColorScreen,
                    HostPickColorScreen2, ClientPickColorScreen2,
                    HostGameScreen, ClientGameScreen,
                    HostGameScreen2, ClientGameScreen2)

def test_ray_intersect():
    from screens.screen import TestRayIntersectSphere

    pygame.init()
    pygame.display.set_caption('Orbits clone')
    settings = {'fullscreen': False,
                'language': 'en'}
    if settings['fullscreen']:
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window_surface = pygame.display.set_mode((600, 300), pygame.RESIZABLE)


    tris = TestRayIntersectSphere(window_surface)
    tris.main()

def main():
    pygame.init()
    pygame.display.set_caption('Orbits clone')
    settings = {'fullscreen': False,
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
            hpcs = HostPickColorScreen2(window_surface, True)
            result = hpcs.main()
            if hpcs.force_quit:
                return
            hgs = HostGameScreen2(window_surface, *result)
            hgs.main()

        elif len(parts) == 3 and parts[1] == 'client':
            cpcs = ClientPickColorScreen2(window_surface, True, parts[2])
            result = cpcs.main()
            if cpcs.force_quit:
                return
            cgs = ClientGameScreen2(window_surface, *result)
            cgs.main()


if __name__ == '__main__':
    main()
    # test_ray_intersect()
