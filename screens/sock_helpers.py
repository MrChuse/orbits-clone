import socket

from back import Team

def send_int(sock: socket.socket, message: int):
    sock.sendall(message.to_bytes(4, 'little'))
    print('sent int', message)
    # response = str(sock.recv(2), 'ascii')
    # print("Received: {}".format(response))

def send_text(sock: socket.socket, message):
    sock.sendall(bytes(message, 'ascii'))
    print('sent str', message)
    # response = str(sock.recv(2), 'ascii')
    # print("Received: {}".format(response))

def recv_int(sock):
    i = int.from_bytes(sock.recv(4), 'little')
    print('recv int', i)
    # sock.sendall(b'OK')
    return i

def recv_player(sock):
    key = recv_int(sock)
    team = recv_int(sock)
    team = list(Team)[team]
    print('recv plr', key, team)
    return key, team