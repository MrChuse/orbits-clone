import socket
import logging
from socketserver import BaseRequestHandler, ThreadingTCPServer
import threading
from typing import Any, Callable
import time

from networking_stuff import RememberingClientsTCPRequestHandler, RememberingClientsTCPServer

class Server(RememberingClientsTCPServer):
    def __init__(self, server_address, client_port, RequestHandlerClass: Callable[[Any, Any, Any], BaseRequestHandler], bind_and_activate: bool = True) -> None:
        super().__init__(server_address, client_port, RequestHandlerClass, bind_and_activate)
        self.received = []
class Handler(RememberingClientsTCPRequestHandler):
    server_class = Server
    def handle(self) -> None:
        super().handle()
        while True:
            data = self.request.recv(10)
            # logging.info('received', data)
            self.server.received.append(data)

server = Server(("0.0.0.0", 9001), 9002, Handler)

ip, port = server.server_address

server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
logging.info(f"Server {ip}:{port}, loop running in thread:", server_thread.name)


start_time = time.time()
greater_than_time = 5
while True:
    current_time = time.time()-start_time
    for recv in server.received:
        logging.info(f'received {recv}, {current_time:.1f}')
    server.received = []

    if current_time > greater_than_time:
        logging.info('sent to all clients', current_time)
        server.sendall_to_all_clients(b'hello world')
        greater_than_time += 5
    # logging.info(current_time)
    time.sleep(1)
