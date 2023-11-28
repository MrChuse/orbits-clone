from typing import Callable, Any
from dataclasses import dataclass
import socket
import socketserver
from socketserver import BaseRequestHandler, ThreadingTCPServer

import pygame

from . import send_command, recv_command, Command

@dataclass
class Client:
    addr: Any
    socket: socket.socket

class RememberingClientsTCPServer(ThreadingTCPServer):
    daemon_threads = True
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.clients: list[Client] = []

    def on_connect(self, addr):
        print('Client connected from', addr)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((addr[0], 9002))
        except ConnectionRefusedError as e:
            print(addr, e)
            return

        client = Client(addr, sock)
        self.clients.append(client)

    def on_disconnect(self, client):
        self.clients.remove(client)
        print('Client disconnected', client.addr)

    def sendall_to_all_clients(self, data: bytes):
        for client in self.clients:
            try:
                client.socket.sendall(data)
            except ConnectionResetError:
                self.on_disconnect(client)

class RememberingClientsTCPRequestHandler(BaseRequestHandler):
    server_class = RememberingClientsTCPServer
    def handle(self) -> None:
        if not isinstance(self.server, self.server_class):
            raise TypeError(f'Can only handle requests of {self.server_class.__name__}')
        addr = self.client_address
        self.server.on_connect(addr)


class HostThreadingTCPServer(ThreadingTCPServer):
    daemon_threads = True
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.clients: list = []
        self.client_sockets: list[socket.socket] = []
        self.client_captures: list[tuple[int, int, str]] = []
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.seed = None

    def send_commands_to_all_clients(self, commands: list[Command]):
        for sock in self.client_sockets:
            for command, value in commands:
                try:
                    send_command(sock, command, value)
                except ConnectionResetError:
                    self.client_sockets.remove(sock)
                    print('client disconnected')

class HostThreadedTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        if not isinstance(self.server, HostThreadingTCPServer):
            raise TypeError('Can only handle requests of HostThreadingTCPServer')

        addr = self.client_address
        print('Client connected from', addr)
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
                if command == '':
                    break
                if command != Command.KEY:
                    continue
                self.server.client_captures.append((client_number, data, f'client{client_number} {pygame.key.name(data)}'))
            except ConnectionAbortedError as e:
                self.server.on_disconnect(self.request, client_number)
                break
