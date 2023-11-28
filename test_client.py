from collections.abc import Callable
import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
import threading
from typing import Any, Callable
import time

from networking_stuff import ConnectingThreadingTCPRequestHandler, ConnectingThreadingTCPServer

class Client(ConnectingThreadingTCPServer):
    daemon_threads = True
    def __init__(self, connect_to_address, server_address, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], bind_and_activate: bool = True) -> None:
        super().__init__(connect_to_address, server_address, RequestHandlerClass, bind_and_activate)
        self.received = []
class Handler(ConnectingThreadingTCPRequestHandler):
    server_class = Client
    def handle(self) -> None:
        super().handle()
        while True:
            data = self.request.recv(11)
            # print('HANDLER: received', data)
            self.server.received.append(data)
            # print('HANDLER: server.received', self.server.received)

server = Client(("127.0.0.1", 9001), ('0.0.0.0', 9002), Handler)

ip, port = server.server_address

server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
print(f"Server {ip}:{port}, loop running in thread:", server_thread.name)


start_time = time.time()
greater_than_time = 3
while True:
    current_time = time.time()-start_time
    for recv in server.received:
        print(f'MAIN: received {recv}, {current_time:.1f}')
    server.received = []

    if current_time > greater_than_time:
        print('MAIN: send to server', current_time)
        server.sendall_to_server(b'hello back')
        greater_than_time += 3

    # print(current_time)
    time.sleep(1)
