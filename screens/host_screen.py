import socket
import socketserver
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import Any, Callable
import threading
import random
import pickle

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team
from .sock_helpers import send_command, recv_command, Command

ThreadingTCPServer.daemon_threads = True
class HostThreadingTCPServer(ThreadingTCPServer):
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.clients: list = []
        self.client_sockets: list[socket.socket] = []
        self.client_captures: list[tuple[int, int, str]] = []
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.seed = None

class HostThreadedTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        addr = self.client_address
        print('handling with a server', addr)
        if addr not in self.server.clients:
            self.server.clients.append(addr)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.client_sockets.append(sock)
            try:
                sock.connect((addr[0], 9002))
            except ConnectionRefusedError as e:
                print(addr, e)
                return
            self.server.on_connect(sock)

        client_number = self.server.clients.index(addr)
        while True:
            try:
                command, data = recv_command(self.request)
                if command != Command.KEY:
                    continue
                self.server.client_captures.append((client_number, data, f'client{client_number} {pygame.key.name(data)}'))
            except ConnectionAbortedError as e:
                self.server.on_disconnect(self.request, client_number)
                break


class HostPickColorScreen(PickColorScreen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        HOST, PORT = "localhost", 9001

        self.server = HostThreadingTCPServer((HOST, PORT), HostThreadedTCPRequestHandler, self.on_connect, self.on_disconnect)

        ip, port = self.server.server_address

        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        print(f"Server {ip}:{port}, loop running in thread:", server_thread.name)

    def on_connect(self, sock: socket.socket):
        send_command(sock, Command.PLA, len(self.key_map))
        l = list(Team)
        for key, (team, name) in self.key_map.items():
            send_command(sock, Command.KEY, key)
            send_command(sock, Command.TEA, l.index(team))

    def on_disconnect(self, sock: socket.socket, client_number):
        self.server.clients.pop(client_number)
        to_delete = []
        for key, (team, name) in self.key_map.items():
            if name.startswith(f'client{client_number}'):
                to_delete.append(key)
        for key in to_delete:
            del self.key_map[key]

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.captured_keys.append((event.key, pygame.key.name(event.key)))

    def send_to_all_clients(self, commands: list):
        for sock in self.server.client_sockets:
            for command, value in commands:
                send_command(sock, command, value)

    def update(self, time_delta):
        commands = []
        # host's presses
        for key, name in self.captured_keys:
            if key == pygame.K_SPACE:
                self.server.seed = random.randint(0, 1000000000)
                if len(self.key_map) >= 2 and self.is_running:
                    self.return_value = self.key_map, self.server
                    print(self.return_value)
                    self.is_running = False
                    commands.append((Command.STR, key))
                    commands.append((Command.SEE, self.server.seed))
            else:
                commands.append((Command.KEY, key))
        self.send_to_all_clients(commands)

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
            print('server.seed is None :(')
        super().__init__(surface, colors, server.seed)
        self.server = server

    def clean_up(self):
        print('shutdown')
        self.server.shutdown()
        for sock in self.server.client_sockets:
            sock.close()

    def send_to_all_clients(self, commands: list):
        for sock in self.server.client_sockets:
            for command, value in commands:
                send_command(sock, command, value)

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
        state = self.game.get_state()

        state_bytes = pickle.dumps(state)
        commands.append((Command.STL, len(state_bytes)))
        commands.append((Command.STT, state_bytes))

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



        self.send_to_all_clients(commands)
        # clients' presses
        for client_id, key, name in self.server.client_captures:
            for id, sock in enumerate(self.server.client_sockets):
                if client_id != id:
                    send_command(sock, Command.KEY, key)
                self.actions.append(key)
        self.server.client_captures = []
        super().update(time_delta)
