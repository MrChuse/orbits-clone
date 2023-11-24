import socket
import socketserver
from socketserver import BaseRequestHandler
from typing import Any, Callable
import threading

import pygame

from .screen import PickColorScreen, GameScreen
from back import Team
from .sock_helpers import send_int, send_text

class HostThreadingTCPServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.clients: list = []
        self.client_sockets: list[socket.socket] = []
        self.client_captures: list[tuple[int, int, str]] = []
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

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
            # data = str(self1.request.recv(1024), 'ascii')
            try:
                data = int.from_bytes(self.request.recv(4), 'little')
                if data: # idk why 0 is there but this if is needed! (continue doesn't work too)
                    self.server.client_captures.append((client_number, data, f'client{client_number} {pygame.key.name(data)}'))
                # response = bytes('OK', 'ascii')
                # self.request.sendall(response)
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
        print('on connect')
        send_int(sock, len(self.key_map))
        l = list(Team)
        for key, (team, name) in self.key_map.items():
            send_int(sock, key)
            send_int(sock, l.index(team))

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
            if event.key == pygame.K_SPACE:
                if len(self.key_map) >= 2:
                    self.return_value = self.key_map, self.server
                    for sock in self.server.client_sockets:
                        send_int(sock, event.key)
                    self.is_running = False
            else:
                self.captured_keys.append((event.key, pygame.key.name(event.key)))


    def update(self, time_delta):
        # host's presses
        for key, name in self.captured_keys:
            for sock in self.server.client_sockets:
                send_int(sock, key)
        # clients' presses
        for client_id, key, name in self.server.client_captures:
            for id, sock in enumerate(self.server.client_sockets):
                if client_id != id:
                    send_int(sock, key)
                self.captured_keys.append((key, name))
        self.server.client_captures = []
        super().update(time_delta)

class HostGameScreen(GameScreen):
    def __init__(self, surface: pygame.Surface, colors, server):
        super().__init__(surface, colors)
        self.server: HostThreadingTCPServer = server

    def clean_up(self):
        print('shutdown')
        self.server.shutdown()
        for sock in self.server.client_sockets:
            sock.close()

    def update(self, time_delta):
        # host's presses
        for key in self.actions:
            for sock in self.server.client_sockets:
                send_int(sock, key)
        # clients' presses
        for client_id, key, name in self.server.client_captures:
            for id, sock in enumerate(self.server.client_sockets):
                if client_id != id:
                    send_int(sock, key)
                self.actions.append(key)
        self.server.client_captures = []
        super().update(time_delta)
