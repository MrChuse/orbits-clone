import socket
import struct
from enum import Enum
import logging

from back import Team, Sphere

class Command(Enum):
    ACK = 'ack' # ACKnowledged
    KEY = 'key' # KEY pressed
    PLA = 'pla' # PLAyers number
    TEA = 'tea' # TEAm
    STR = 'str' # STaRt
    SEE = 'see' # SEEd
    STL = 'stl' # STate Length
    STT = 'stt' # STaTe
    RES = 'res' # restart
    REC = 'rec' # RECeive
    COM = 'com' # COMmands number
    # ROT = 'rot' # ROTators
    # SPH = 'sph' # SPHere
    # PSX = 'psx' # PoSitionX
    # PSY = 'psy' # PoSitionY
    # VLX = 'vlx' # VeLocityX
    # VLY = 'vly' # VeLocityY
    # RAD = 'rad' # RADIUS
    # CLR = 'clr' # CoLor Red
    # CLG = 'clg' # CoLor Green
    # CLB = 'clb' # CoLor Blue

# def commands_for_sphere(self, sphere: Sphere):
#     return [((Command.SPH, 8)),
#     ((Command.PSX, sphere.center.x)),
#     ((Command.PSY, sphere.center.y)),
#     ((Command.PSY, sphere.velocity.x)),
#     ((Command.PSY, sphere.velocity.y)),
#     ((Command.RAD, sphere.radius)),
#     ((Command.CLR, sphere.color[0])),
#     ((Command.RAD, sphere.color[1])),
#     ((Command.RAD, sphere.color[2])),
#     ]

def send_command(sock: socket.socket, command: Command, value):
    if command == Command.STT:
        send_command(sock, Command.STL, len(value))
        send_text(sock, command.value)
        sock.sendall(value)
        # logging.info(f'send {command.value} {len(value)} bytes')
    else:
        send_text(sock, command.value)
        send_int(sock, value)
        # if command not in (Command.REC, Command.COM):
        # logging.info(f'send {command.value} {value}')

def recv_command(sock: socket.socket, *args):
    # logging.info('trying to recv command')
    command = recv_text(sock, 3)
    try:
        command = Command(command)
    except Exception as e:
        logging.info(e)
    if isinstance(command, Command):
        if command == Command.STL:
            value = recv_int(sock)
            return recv_command(sock, value)
        elif command == Command.STT:
            received_length = 0
            need_to_receive = args[0]
            value = b''
            while received_length < args[0]: # may not receive in one go
                received = sock.recv(need_to_receive)
                # logging.info('recv', command.value, len(received))
                value += received
                received_length += len(received)
                need_to_receive -= len(received)
        else:
            value = recv_int(sock)
            # if command not in (Command.COM, Command.REC):
            # logging.info(f'recv {command.value} {value}')
    else:
        value = recv_int(sock)
        # logging.info(f'recv {command} {value}')

    return command, value


def send_int(sock: socket.socket, message: int):
    sock.sendall(message.to_bytes(4, 'little'))
    # logging.info('send int', message)

def recv_int(sock: socket.socket):
    rcv = sock.recv(4)
    i = int.from_bytes(rcv, 'little')
    # logging.info('recv int', rcv, i)
    return i

def send_float(sock: socket.socket, message: float):
    sock.sendall(struct.pack("d", message))

def recv_float(sock: socket.socket, message: float):
    f = struct.unpack('d', sock.recv(8))
    return f

def send_text(sock: socket.socket, message):
    sock.sendall(bytes(message, 'ascii'))
    # logging.info('send str', message)

def recv_text(sock: socket.socket, length):
    data = str(sock.recv(length), 'ascii')
    # logging.info('recv str', data)
    return data

def recv_player(sock: socket.socket):
    command, key = recv_command(sock)
    assert command == Command.KEY, f'command {command} was not KEY'
    command, team = recv_command(sock)
    assert command == Command.TEA, f'command {command} was not TEA'
    team = list(Team)[team]
    # logging.info('recv plr', key, team)
    return key, team

# def recv_sphere(sock: socket.socket):
#     command, future_commands = recv_command(sock)
#     assert command == Command.SPH and future_commands == 8
#     command, posx = recv_command(sock)
#     assert command == Command.PSX
#     command, posy = recv_command(sock)
#     assert command == Command.PSY
#     command, velx = recv_command(sock)
#     assert command == Command.VLX
#     command, vely = recv_command(sock)
#     assert command == Command.VLY
#     command, radius = recv_command(sock)
#     assert command == Command.RAD
#     command, red = recv_command(sock)
#     assert command == Command.CLR
#     command, green = recv_command(sock)
#     assert command == Command.CLG
#     command, blue = recv_command(sock)
#     assert command == Command.CLB
#     return (posx, posy), (velx, vely), radius, (red, green, blue)

from .host_server import HostThreadedTCPRequestHandler, HostThreadingTCPServer
from .client_server import ClientThreadedTCPRequestHandler, ClientThreadingTCPServer
from .host_server import RememberingClientsTCPRequestHandler, RememberingClientsTCPServer
from .client_server import ConnectingThreadingTCPRequestHandler, ConnectingThreadingTCPServer
