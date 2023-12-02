from collections.abc import Callable
from typing import Callable, Any
import socket
import socketserver
from socketserver import BaseRequestHandler, ThreadingTCPServer
import pickle
import logging

import pygame

from . import recv_command, Command

class ConnectingThreadingTCPServer(ThreadingTCPServer):
    def __init__(self, connect_to_address, server_address, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], bind_and_activate: bool = True) -> None:
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_sock.connect(connect_to_address)

        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

    def on_connect(self, addr):
        logging.info('server connected back')

    def sendall_to_server(self, data):
        self.send_sock.sendall(data)

class ConnectingThreadingTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        if not isinstance(self.server, ConnectingThreadingTCPServer):
            raise TypeError('Can only handle requests of ConnectingThreadingTCPServer')
        addr = self.client_address
        self.server.on_connect(addr)



class ClientThreadedTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        if not isinstance(self.server, ClientThreadingTCPServer):
            raise TypeError('Can only handle requests of ClientThreadingTCPServer')

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

class ClientThreadingTCPServer(ThreadingTCPServer):
    daemon_threads = True
    def __init__(self, server_address: Any, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], on_connect, on_disconnect, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.captured_keys: list[tuple[int, str]] = []
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.seed = None
        self.game_state = None
        self.restart = False