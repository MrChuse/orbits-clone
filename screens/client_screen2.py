import socket
import pickle
import logging

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team, PlayerSphere
from networking_stuff import recv_player, send_command, recv_command, Command, ClientThreadingTCPServer, ClientThreadedTCPRequestHandler

class SocketClient:
    def __init__(self, address):
        self.address = address

class ClientPickColorScreen2(PickColorScreen):
    def __init__(self, surface: pygame.Surface, host, port=9001):
        super().__init__(surface, draw_bots_buttons=False)
        self.host = host
        self.port = port
        self.seed = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except (ConnectionRefusedError, TimeoutError) as e:
            logging.info(e)
        else:
            self.on_connect(self.sock)

    def on_connect(self, sock):
        command, number_of_players = recv_command(sock)
        if command != Command.PLA:
            logging.info('error:', command, 'was not PLA')
        logging.info(f'{number_of_players=}')
        for i in range(number_of_players):
            key, team = recv_player(sock)
            self.key_team_iter_map[key] = iter(Team)
            iter_team = next(self.key_team_iter_map[key])
            while iter_team != team:
                iter_team = next(self.key_team_iter_map[key])
            self.key_map[key] = team, f'host {pygame.key.name(key)}', PlayerSphere
            self.unavailable_teams.append(team)
            self.order.append(key)

    def on_disconnect(self):
        to_delete = []
        for key, (team, name, PlayerClass) in self.key_map.items():
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
        send_command(self.sock, Command.REC, 0)
        command, value = recv_command(self.sock)
        if command == '':
            self.on_disconnect()
            super().update(time_delta)
            return
        assert command == Command.COM, repr(command)
        for _ in range(value):
            command, value = recv_command(self.sock)
            if command == Command.KEY:
                self.captured_keys.append((value, f'host {pygame.key.name(value)}'))
            elif command == Command.STR:
                self.captured_keys.append((value, f'host {pygame.key.name(value)}'))
            elif command == Command.SEE:
                self.seed = value
        for key, team in self.captured_keys:
            if key == pygame.K_SPACE:
                self.return_value = self.key_map, self.sock, self.seed
                self.is_running = False
        super().update(time_delta)

class ClientGameScreen2(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, sock, seed):
        if seed is None:
            logging.info('server.seed is None :(')
        super().__init__(surface, colors, seed)
        self.sock: socket.socket = sock

    def clean_up(self):
        logging.info('shutdown')
        self.sock.close()

    def update(self, time_delta):
        for key in self.actions:
            send_command(self.sock, Command.KEY, key)
        send_command(self.sock, Command.REC, 0)
        command, value = recv_command(self.sock)
        if command == '':
            super().update(time_delta)
            return
        assert command == Command.COM, repr(command)
        length_of_state = None
        for _ in range(value):
            if length_of_state is None:
                command, value = recv_command(self.sock)
            else:
                command, value = recv_command(self.sock, length_of_state)
                length_of_state = None
            if command == Command.KEY:
                self.actions.append(value)
            elif command == Command.STL:
                length_of_state = value
            elif command == Command.STT:
                self.game.set_state(pickle.loads(value))
            elif command == Command.RES:
                self.game.restart_round()
        super().update(time_delta)