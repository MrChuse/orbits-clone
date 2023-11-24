# from _socket import _RetAddress
from collections.abc import Callable
import socket
import socketserver
# from socketserver import _AfInetAddress,BaseRequestHandler
from socketserver import BaseRequestHandler
import threading
from traceback import print_exc
from collections import deque
from typing import Any

import pygame
import pygame.freetype
pygame.freetype.init()
import pygame_gui
from pygame_gui.elements import UIButton, UITextEntryLine
from pygame_gui.windows import UIMessageWindow

from back import Game, Team
from front import draw_game

font = pygame.freetype.SysFont('arial', 25)

class Screen:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.return_value = None
        self.force_quit = False

    def clean_up(self):
        return
    def process_events(self, event):
        return
    def update(self, time_delta):
        return

    def main(self):
        window_size = self.surface.get_rect().size
        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#101010'))

        clock = pygame.time.Clock()
        self.is_running = True
        while self.is_running:
            time_delta = clock.tick(60)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.force_quit = True
                    self.is_running = False
                self.process_events(event)

            self.surface.blit(background, (0, 0))
            self.update(time_delta)
            pygame.display.update()
        self.clean_up()
        return self.return_value


def inscribed_rectangle_dimensions(w, h):
    vertical_side = min(w, h / 2)
    horizontal_side = min(w / 2, h)
    if horizontal_side > vertical_side:
        return 2 * horizontal_side, horizontal_side
    else:
        return vertical_side, 2 * vertical_side

class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface, colors):
        super().__init__(surface)
        self.colors = colors
        self.game = None
        self.window_size = self.surface.get_rect().size
        self.manager = pygame_gui.UIManager(self.window_size, 'theme.json', enable_live_theme_updates=False)
        self.visual_debug = False
        self.game_size = inscribed_rectangle_dimensions(*self.window_size)
        borderx = (self.window_size[0] - self.game_size[0]) / 2
        bordery = (self.window_size[1] - self.game_size[1]) / 2
        self.game_surface_margin = borderx, bordery
        self.game = Game(colors)
        self.game_surface = pygame.Surface(self.game_size)
        self.is_paused = False
        self.by_step = False
        self.actions = []

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_ALT:
                self.visual_debug = not self.visual_debug
                self.manager.set_visual_debug_mode(self.visual_debug)
            if event.key in self.colors.keys():
                self.actions.append(event.key)
            if event.key == pygame.K_F2:
                self.is_paused = not self.is_paused
            if event.key == pygame.K_F3:
                self.by_step = True
                self.is_paused = True
        elif event.type == pygame.WINDOWSIZECHANGED:
            if event.window is None:
                self.manager.set_window_resolution((event.x, event.y))
                # cursor_manager.set_window_resolution((event.x, event.y))
                background = pygame.Surface((event.x, event.y))
                background.fill(pygame.Color('#000000'))
                if self.game is not None:
                    self.game.set_dimensions((event.x, event.y))
            self.manager.process_events(event)

    def update(self, time_delta):
            self.game_surface.fill(pygame.Color('#000000'))
            self.manager.update(time_delta)
            if self.game is not None:
                if not self.is_paused or self.by_step:
                    self.game.process_actions(self.actions)
                    self.game.update(time_delta)
                    self.actions = []
                    self.by_step = False

                state = self.game.get_state()
                draw_game(self.game_surface, state, self.game_size)
                # self.game.draw_debug(self.game_surface)
            self.surface.blit(self.game_surface, self.game_surface_margin)
            self.manager.draw_ui(self.surface)
    # finally:
    #     if game is not None:
    #         game.exit()


class PickColorScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.key_map : dict[int, Team] = {}
        self.key_team_iter_map = {}
        self.unavailable_teams = []
        self.order = []
        self.captured_keys = []

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if len(self.key_map) >= 2:
                    self.return_value = self.key_map
                    self.is_running = False
            else:
                self.captured_keys.append((event.key, pygame.key.name(event.key)))

    def process_player_action(self, key, name):
        if key not in self.key_team_iter_map:
            self.key_team_iter_map[key] = iter(Team)
        if key in self.key_map:
            team, name = self.key_map.pop(key)
            self.unavailable_teams.remove(team)
        elif len(self.unavailable_teams) < len(Team):
            team = None
            while True:
                try:
                    team = next(self.key_team_iter_map[key])
                    if team in self.unavailable_teams:
                        continue
                    self.key_map[key] = team, name
                    self.unavailable_teams.append(team)
                    break
                except StopIteration:
                    self.key_team_iter_map[key] = iter(Team)
            if key not in self.order:
                self.order.append(key)

    def update(self, time_delta):
        for key, name in self.captured_keys:
            self.process_player_action(key, name)
        self.captured_keys = []

        size = self.surface.get_rect().size
        surf1, textsize1 = font.render('PRESS BUTTONS', (255, 255, 255), size=32)
        surf2, textsize2 = font.render('then hit space', (255, 255, 255), size=32)
        self.surface.blit(surf1, (30, 30))
        self.surface.blit(surf2, (30, size[1] - 30 - textsize2[1]))
        for key, (team, name) in self.key_map.items():
            i = self.order.index(key)
            pygame.draw.ellipse(self.surface, team.value, (100+100*(2*i//len(Team)), 100 + 60*(i%(len(Team)//2)), 25, 25))
            font.render_to(self.surface, (130+100*(2*i//len(Team)), 100 + 60 * (i%(len(Team)//2)), 25, 25), name, team.value)


class LocalOnlinePickerScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.manager = pygame_gui.UIManager(surface.get_rect().size)
        rect1 = pygame.Rect(surface.get_rect())
        rect1 = rect1.inflate(-200, -200)
        rect1.height /= 2
        self.local_button = UIButton(rect1, 'Local', manager=self.manager,)
        rect2 = pygame.Rect((0, 0), rect1.size)
        # rect2.bottomright = -100, -100
        self.online_button = UIButton(rect2, 'Online', manager=self.manager,
                                      anchors={'centerx': 'centerx',
                                            'top_target': self.local_button})
        rect3 = pygame.Rect(rect2)
        rect3.left = rect1.left
        rect3.width /= 2
        self.host_button = UIButton(rect3, 'Host', self.manager, visible=False,
                                    anchors={'top_target': self.local_button})
        rect4 = pygame.Rect(rect3)
        rect4.left = 0
        rect4.height -= 30
        self.client_button = UIButton(rect4, 'Connect', self.manager, visible=False,
                                    anchors={'top_target': self.local_button,
                                            'left_target':self.host_button})
        self.placeholder_ip = '127.0.0.1'
        self.client_text_entry = UITextEntryLine(pygame.Rect(0, 0, rect4.width, 30), self.manager,
                                                 visible=False, placeholder_text=self.placeholder_ip,
                                                 anchors={'top_target': self.client_button,
                                                          'left_target':self.host_button})

    def process_events(self, event):
        self.manager.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.local_button:
                self.return_value = 'local'
                self.is_running = False
            elif event.ui_element == self.online_button:
                self.online_button.hide()
                self.host_button.show()
                self.client_button.show()
                self.client_text_entry.show()
            elif event.ui_element == self.host_button:
                self.return_value = 'online host'
                self.is_running = False
            elif event.ui_element == self.client_button:
                text = self.client_text_entry.text
                if not text:
                    text = self.placeholder_ip
                try:
                    socket.inet_aton(text)
                except socket.error as e:
                    rect = pygame.Rect(self.surface.get_rect())
                    rect = rect.scale_by(0.5, 0.5)
                    UIMessageWindow(rect, f'{text} is an invalid IPv4 address')
                else:
                    self.return_value = f'online client {text}'
                    self.is_running = False

    def update(self, time_delta):
        self.manager.update(time_delta)
        self.manager.draw_ui(self.surface)
