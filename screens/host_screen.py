import socket
import threading
import random
import pickle
import logging

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team
from networking_stuff import send_command, Command, HostThreadingTCPServer, HostThreadedTCPRequestHandler

class HostPickColorScreen(PickColorScreen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface, draw_bots_buttons=False)
        HOST, PORT = "0.0.0.0", 9001

        self.server = HostThreadingTCPServer((HOST, PORT), HostThreadedTCPRequestHandler, self.on_connect, self.on_disconnect)

        ip, port = self.server.server_address

        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        logging.info(f"Server {ip}:{port}, loop running in thread:", server_thread.name)

    def on_connect(self, sock: socket.socket):
        send_command(sock, Command.PLA, len(self.key_map))
        l = list(Team)
        logging.info(self.key_map)
        for key, (team, name, PlayerClass) in self.key_map.items():
            send_command(sock, Command.KEY, key)
            send_command(sock, Command.TEA, l.index(team))

    def on_disconnect(self, sock: socket.socket, client_number):
        self.server.clients.pop(client_number)
        to_delete = []
        for key, (team, name, PlayerClass) in self.key_map.items():
            if name.startswith(f'client{client_number}'):
                to_delete.append(key)
        for key in to_delete:
            del self.key_map[key]

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.captured_keys.append((event.key, pygame.key.name(event.key)))

    def update(self, time_delta):
        commands = []
        # host's presses
        for key, name in self.captured_keys:
            if key == pygame.K_SPACE:
                self.server.seed = random.randint(0, 1000000000)
                if len(self.key_map) >= 2 and self.is_running:
                    self.return_value = self.key_map, self.server
                    self.is_running = False
                    commands.append((Command.STR, key))
                    commands.append((Command.SEE, self.server.seed))
            else:
                commands.append((Command.KEY, key))
        self.server.send_commands_to_all_clients(commands)

        # clients' presses
        for client_id, key, name in self.server.client_captures:
            for id, sock in enumerate(self.server.client_sockets):
                if client_id != id: # this stupid if doesn't allow send_to_all_clients
                    send_command(sock, Command.KEY, key)
                self.captured_keys.append((key, name))
        self.server.client_captures = []
        super().update(time_delta)

class HostGameScreen(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, server: HostThreadingTCPServer):
        if server.seed is None:
            logging.info('server.seed is None :(')
        super().__init__(surface, colors, server.seed)
        self.server = server
        self.send_state_every_seconds = 1
        self.send_state_timer = self.send_state_every_seconds
        self.timer = 0

    def clean_up(self):
        logging.info('shutdown')
        self.server.shutdown()
        for sock in self.server.client_sockets:
            sock.close()

    def update(self, time_delta):
        commands = []

        if self.restart:
            new_seed = random.randint(0, 1000000000)
            commands.append((Command.RES, new_seed))
            self.game.restart_round(new_seed)
            self.restart = False

        # host's presses
        for key in self.actions:
            for sock in self.server.client_sockets:
                commands.append((Command.KEY, key))

        # collect state
        if self.timer >= self.send_state_timer:
            state = self.game.get_state()

            state_bytes = pickle.dumps(state)
            commands.append((Command.STL, len(state_bytes)))
            commands.append((Command.STT, state_bytes))
            self.send_state_timer += self.send_state_every_seconds
        self.timer += time_delta

        # think about json-serialization
        # {'rotators': self.rotators,
        # 'players': self.player_spheres,
        # 'spheres': self.spheres,
        # 'someone_won': self.someone_won,
        # }

        # state_commands.append((Command.ROT, len(state['rotators'])))
        # for rotator in state['rotators']:
        #     state_commands.extend(commands_for_sphere(rotator))
        # state_commands.append((Command.PLA, len(state['player_spheres'])))
        # for player in state['player_spheres']:
        #     state_commands.extend(commands_for_sphere(player))
        #     for

        self.server.send_commands_to_all_clients(commands)
        # clients' presses
        for client_id, key, name in self.server.client_captures:
            for id, sock in enumerate(self.server.client_sockets):
                if client_id != id:
                    send_command(sock, Command.KEY, key)
                self.actions.append(key)
        self.server.client_captures = []
        super().update(time_delta)
