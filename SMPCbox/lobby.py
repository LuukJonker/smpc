import socket
import threading
import json
from dataclasses import dataclass

MCAST_GROUP = "224.1.1.1"
MCAST_PORT = 5007
DISCOVERY_MSG = "DISCOVER_PEER"
ANNOUNCE_MSG = "ANNOUNCE_PEER"
OFFLINE_MSG = "OFFLINE_PEER"
BUFFER_SIZE = 1024


@dataclass
class Protocol:
    msg_type: str


peers = []

class Host:
    def __init__(self, name: str) -> None:
        self.name = name
        self.server_socket: socket.socket
        self.multicast_socket: socket.socket
        self.port: int

    def serve(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", 0))  # Bind to a random available port
        self.port = self.server_socket.getsockname()[1]
        self.server_socket.listen(5)

        threading.Thread(
            target=self.broadcast_announcement,
            args=(
                name,
                self.port,
            ),
        ).start()

        while True:
            peer_socket, address = self.server_socket.accept()
            print(f"Connection from {address} has been established.")
            peers.append((peer_socket, address))


    def broadcast_announcement(self):
        self.multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        info = json.dumps({"msg_type": ANNOUNCE_MSG, "name": self.name, "port": self.port})

        while True:
            msg = self.multicast_socket.recv(BUFFER_SIZE).decode("utf-8")
            if msg == DISCOVERY_MSG:
                self.multicast_socket.sendto(info.encode("utf-8"), (MCAST_GROUP, MCAST_PORT))


def listen_for_peers():
    multicast_socket = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
    )
    multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_socket.bind((MCAST_GROUP, MCAST_PORT))

    mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        message, address = multicast_socket.recvfrom(BUFFER_SIZE)
        msg_parts = message.decode("utf-8").split(":")

        if msg_parts[0] == ANNOUNCE_MSG:
            peer_ip = address[0]
            peer_port = int(msg_parts[1])
            if (peer_ip, peer_port) not in [(addr[1][0], addr[1][1]) for addr in peers]:
                connect_to_peer(peer_ip, peer_port)


def connect_to_peer(peer_ip, peer_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, peer_port))
    peers.append((client_socket, (peer_ip, peer_port)))

    def listen_to_peer():
        while True:
            try:
                message = client_socket.recv(BUFFER_SIZE).decode("utf-8")
                print(message)
            except:
                print("Connection to peer lost.")
                client_socket.close()
                break

    listen_thread = threading.Thread(target=listen_to_peer)
    listen_thread.start()


def broadcast_discovery():
    multicast_socket = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
    )
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    multicast_socket.sendto(
        f"{DISCOVERY_MSG}".encode("utf-8"), (MCAST_GROUP, MCAST_PORT)
    )

def start_server(name):
    Host(name)

if __name__ == "__main__":
    mode = input("Enter mode (host/join): ")

    if mode == "host":
        name = input("Enter the name: ")
        threading.Thread(target=start_server, args=(name,)).start()
    elif mode == "join":
        threading.Thread(target=listen_for_peers).start()
        broadcast_discovery()
        while True:
            command = input(
                "Enter command (REFRESH to find new peers, LIST to list peers): "
            )
            if command == "REFRESH":
                broadcast_discovery()
            elif command == "LIST":
                for peer_socket, addr in peers:
                    print(f"Connected to {addr[0]}:{addr[1]}")
