import socket
import socketserver
from socketserver import BaseRequestHandler
import threading
from typing import Any, Callable
import pickle

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team
from .sock_helpers import recv_player, send_command, recv_command, Command

class ClientThreadedTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        self.server.on_connect(self.request)
        while True:
            try:
                command, data = recv_command(self.request)
                if command == Command.KEY:
                    self.server.captured_keys.append((data, f'host {pygame.key.name(data)}'))
                elif command == Command.STR:
                    self.server.captured_keys.append((data, f'host {pygame.key.name(data)}'))
                    command, data = recv_command(self.request)
                    assert command == Command.SEE
                    self.server.seed = data
                elif command == Command.STL:
                    command, data = recv_command(self.request, data)
                    assert command == Command.STT
                    self.server.game_state = pickle.loads(data)
                elif command == Command.RES:
                    self.server.seed = data
                    self.server.restart = True
                elif command == '':
                    break
            except ConnectionAbortedError as e:
                self.server.on_disconnect(self.request)
                break

class ClientThreadingTCPServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.captured_keys: list[tuple[int, str]] = []
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.seed = None
        self.game_state = None
        self.restart = False

class ClientPickColorScreen(PickColorScreen):
    def __init__(self, surface: pygame.Surface, host, port=9001):
        super().__init__(surface, draw_bots_buttons=False)
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            print(e)


        self.server = ClientThreadingTCPServer(('0.0.0.0', 9002), ClientThreadedTCPRequestHandler, self.on_connect, self.on_disconnect)
        ip, port = self.server.server_address

        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        print(f"Client {ip}:{port}, loop running in thread:", server_thread.name)

    def on_connect(self, sock):
        command, number_of_players = recv_command(sock)
        if command != Command.PLA:
            print('error:', command, 'was not PLA')
        print(f'{number_of_players=}')
        for i in range(number_of_players):
            key, team = recv_player(sock)
            self.key_team_iter_map[key] = iter(Team)
            iter_team = next(self.key_team_iter_map[key])
            while iter_team != team:
                iter_team = next(self.key_team_iter_map[key])
            self.key_map[key] = team, f'host {pygame.key.name(key)}'
            self.unavailable_teams.append(team)
            self.order.append(key)

    def on_disconnect(self, sock):
        to_delete = []
        for key, (team, name) in self.key_map.items():
            if name.startswith(f'host'):
                to_delete.append(key)
        for key in to_delete:
            del self.key_map[key]

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # if len(self.key_map) >= 2:
                #     self.return_value = self.key_map
                #     self.is_running = False
                pass
            else:
                self.captured_keys.append((event.key, pygame.key.name(event.key)))

    def update(self, time_delta):
        for key, name in self.captured_keys:
            send_command(self.sock, Command.KEY, key)
        for key, team in self.server.captured_keys:
            if key == pygame.K_SPACE:
                self.return_value = self.key_map, self.sock, self.server
                self.is_running = False
            else:
                self.captured_keys.append((key, team))
        self.server.captured_keys = []
        super().update(time_delta)

class ClientGameScreen(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, sock, server: ClientThreadingTCPServer,):
        if server.seed is None:
            print('server.seed is None :(')
        super().__init__(surface, colors, server.seed)
        self.sock: socket.socket = sock
        self.server = server

    def clean_up(self):
        print('shutdown')
        self.server.shutdown()
        self.sock.close()

    def update(self, time_delta):
        if self.server.restart:
            self.game.restart_round()
            self.server.restart = False
        for key in self.actions:
            send_command(self.sock, Command.KEY, key)
        for key, team in self.server.captured_keys:
            self.actions.append(key)
        self.server.captured_keys = []
        if self.server.game_state is not None:
            self.game.set_state(self.server.game_state)
            self.server.game_state = None
        super().update(time_delta)