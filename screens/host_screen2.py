import socket
from socketserver import ThreadingTCPServer, BaseRequestHandler
from typing import Callable, Any
import threading
import random
import pickle
import logging

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team
from networking_stuff import send_command, Command, recv_command


class HostMultiplexingThreadingTCPServer(ThreadingTCPServer):
    daemon_threads = True
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.clients_numbers: dict[tuple, int] = {}
        self.commands_to_send: dict[tuple, list] = {}
        self.client_captures: dict[tuple, list] = {}

    def send_commands_to_all_clients(self, commands):
        for l in self.commands_to_send.values():
            l.extend(commands)

    def send_one_command_to_clients_except(self, command, except_client):
        for addr, l in self.commands_to_send.items():
            if addr == except_client: continue
            l.append(command)

class HostMultiplexingThreadingTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        if not isinstance(self.server, HostMultiplexingThreadingTCPServer):
            raise TypeError('Can only handle requests of HostMultiplexingThreadingTCPServer')

        addr = self.client_address
        logging.info(f'Client connected from {addr}')

        self.server.commands_to_send[addr] = []
        self.server.client_captures[addr] = []
        self.server.clients_numbers[addr] = len(self.server.clients_numbers)
        self.server.on_connect(self.request)
        while True:
            command, value = recv_command(self.request)
            if command == Command.KEY:
                self.server.client_captures[addr].append(value)
            elif command == Command.REC:
                commands_to_send = self.server.commands_to_send[addr]
                self.server.commands_to_send[addr] = []
                send_command(self.request, Command.COM, len(commands_to_send))
                for command in commands_to_send:
                    send_command(self.request, *command)
            if command == '':
                break
        self.server.on_disconnect(self.server.clients_numbers[addr])



class HostPickColorScreen2(PickColorScreen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface, draw_bots_buttons=False)
        HOST, PORT = "0.0.0.0", 9001

        self.server = HostMultiplexingThreadingTCPServer((HOST, PORT), HostMultiplexingThreadingTCPRequestHandler, self.on_connect, self.on_disconnect)

        ip, port = self.server.server_address

        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        logging.info(f"Server {ip}:{port}, loop running in thread: {server_thread.name}")

    def on_connect(self, sock: socket.socket):
        send_command(sock, Command.PLA, len(self.key_map))
        l = list(Team)
        logging.info(self.key_map)
        for key, (team, name, PlayerClass) in self.key_map.items():
            send_command(sock, Command.KEY, key)
            send_command(sock, Command.TEA, l.index(team))

    def on_disconnect(self, client_number):
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
        for client_addr, keys in self.server.client_captures.items():
            for key in keys:
                self.server.send_one_command_to_clients_except((Command.KEY, key), client_addr)
                logging.info(f'{key} {client_addr}')
                self.captured_keys.append((key, f'client{self.server.clients_numbers[client_addr]} {pygame.key.name(key)}'))
            keys.clear()
        super().update(time_delta)

class HostGameScreen2(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, server: HostMultiplexingThreadingTCPServer):
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

    def update(self, time_delta):
        commands = []

        if self.restart:
            commands.append((Command.RES, 0))
            self.game.restart_round()
            self.restart = False

        # host's presses
        for key in self.actions:
            commands.append((Command.KEY, key))

        # collect state
        if self.timer >= self.send_state_timer:
            state = self.game.get_state()

            state_bytes = pickle.dumps(state)
            commands.append((Command.STT, state_bytes))
            self.send_state_timer += self.send_state_every_seconds
        self.timer += time_delta

        # think about json-serialization
        # {'rotators': self.rotators,
        # 'players': self.player_spheres,
        # 'spheres': self.spheres,
        # 'someone_won': self.someone_won,
        # 'attacking_spheres': self.attacking_spheres}

        # state_commands.append((Command.ROT, len(state['rotators'])))
        # for rotator in state['rotators']:
        #     state_commands.extend(commands_for_sphere(rotator))
        # state_commands.append((Command.PLA, len(state['player_spheres'])))
        # for player in state['player_spheres']:
        #     state_commands.extend(commands_for_sphere(player))
        #     for

        self.server.send_commands_to_all_clients(commands)
        # clients' presses
        for client_addr, keys in self.server.client_captures.items():
            for key in keys:
                self.server.send_one_command_to_clients_except((Command.KEY, key), client_addr)
                self.actions.append(key)
            keys.clear()
        super().update(time_delta)
