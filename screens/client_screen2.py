import socket
import pickle
import threading
from collections import deque
import logging

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team, PlayerSphere
from networking_stuff import recv_player, send_command, recv_command, Command, ClientThreadingTCPServer, ClientThreadedTCPRequestHandler

class SocketClient:
    def __init__(self, address, on_connect, on_disconnect, framerate=60):
        self.address = address
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.framerate = framerate

        self.commands_to_send = []
        self.commands_received = deque()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(address)
        except (ConnectionRefusedError, TimeoutError) as e:
            logging.info(e)
        client_thread = threading.Thread(target=self.client_forever, daemon=True)
        client_thread.start()
        logging.info(f"Client connects to {address[0]}:{address[1]}, loop running in thread: {client_thread.name}")


    def send_command(self, command, value):
        self.commands_to_send.append((command, value))

    def recv_command(self):
        if len(self.commands_received) > 0:
            return self.commands_received.popleft()
        else:
            return None, None

    def close(self):
        self.sock.close()

    def client_forever(self):
        clock = pygame.Clock()
        self.on_connect(self.sock)
        while True:
            time_delta = clock.tick(self.framerate)
            commands = self.commands_to_send
            self.commands_to_send = []
            for command in commands:
                send_command(self.sock, *command)
            send_command(self.sock, Command.REC, 0)
            command, value = recv_command(self.sock)
            if command == '':
                self.on_disconnect()
                return
            assert command == Command.COM, repr(command)
            for _ in range(value):
                self.commands_received.append(recv_command(self.sock))

class ClientPickColorScreen2(PickColorScreen):
    def __init__(self, surface: pygame.Surface, host, port=9001):
        super().__init__(surface, draw_bots_buttons=False)
        self.host = host
        self.port = port
        self.seed = None
        self.client = SocketClient((self.host, self.port), self.on_connect, self.on_disconnect)

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
            self.client.send_command(Command.KEY, key)
        while len(self.client.commands_received) > 0:
            command, value = self.client.commands_received.popleft()
            if command == Command.KEY:
                self.captured_keys.append((value, f'host {pygame.key.name(value)}'))
            elif command == Command.STR:
                self.captured_keys.append((value, f'host {pygame.key.name(value)}'))
            elif command == Command.SEE:
                self.seed = value
        for key, team in self.captured_keys:
            if key == pygame.K_SPACE:
                self.return_value = self.key_map, self.client, self.seed
                self.is_running = False
        super().update(time_delta)

class ClientGameScreen2(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, client, seed):
        if seed is None:
            logging.info('server.seed is None :(')
        super().__init__(surface, colors, seed)
        self.client: SocketClient = client

    def clean_up(self):
        logging.info('shutdown')
        self.client.close()

    def update(self, time_delta):
        for key in self.actions:
            self.client.send_command(Command.KEY, key)

        while len(self.client.commands_received) > 0:
            command, value = self.client.commands_received.popleft()
            if command == Command.KEY:
                self.actions.append(value)
            elif command == Command.STL:
                length_of_state = value
            elif command == Command.STT:
                self.game.set_state(pickle.loads(value))
            elif command == Command.RES:
                self.game.restart_round()
        super().update(time_delta)