import sys
import socket
import threading
import time
from PyQt5 import QtWidgets
import json
from typing import Any
from enum import Enum

MCAST_GROUP = "224.1.1.1"
MCAST_PORT = 5007
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 5  # seconds
TIMEOUT_INTERVAL = 15  # seconds


class MessageType(Enum):
    DISCOVERY = "DISCOVERY"
    ANNOUNCE = "ANNOUNCE"
    HEARTBEAT = "HEARTBEAT"
    JOIN = "JOIN"


class Message:
    def __init__(self, msg_type: MessageType, data: dict[str, Any]) -> None:
        self.msg_type = msg_type
        self.data = data

    def encode(self) -> bytes:
        data = self.data.copy()
        data["msg_type"] = self.msg_type.value
        return json.dumps(data).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        msg = json.loads(data.decode("utf-8"))
        msg_type = MessageType(msg["msg_type"])
        del msg["msg_type"]

        if msg_type == MessageType.DISCOVERY:
            return DiscoveryMessage()
        elif msg_type == MessageType.ANNOUNCE:
            return AnnounceMessage(msg["name"], msg["port"])
        elif msg_type == MessageType.HEARTBEAT:
            return HeartbeatMessage(msg["port"])
        elif msg_type == MessageType.JOIN:
            return JoinMessage(msg["name"], msg["port"])
        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    def is_discovery(self) -> bool:
        return self.msg_type == MessageType.DISCOVERY

    def is_announce(self) -> bool:
        return isinstance(self, AnnounceMessage)

    def is_heartbeat(self) -> bool:
        return self.msg_type == MessageType.HEARTBEAT

    def is_join(self) -> bool:
        return self.msg_type == MessageType.JOIN


class DiscoveryMessage(Message):
    def __init__(self) -> None:
        super().__init__(MessageType.DISCOVERY, {})


class AnnounceMessage(Message):
    def __init__(self, name: str, port: int) -> None:
        super().__init__(MessageType.ANNOUNCE, {"name": name, "port": port})
        self.name = name
        self.port = port


class HeartbeatMessage(Message):
    def __init__(self, port: int) -> None:
        super().__init__(MessageType.HEARTBEAT, {"port": port})
        self.port = port


class JoinMessage(Message):
    def __init__(self, name: str, port: int) -> None:
        super().__init__(MessageType.JOIN, {"name": name, "port": port})
        self.name = name
        self.port = port


class Client:
    def __init__(self, gui: QtWidgets.QWidget) -> None:
        self.gui = gui

    def refresh(self):
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        multicast_socket.sendto(DiscoveryMessage().encode(), (MCAST_GROUP, MCAST_PORT))


class Host(Client):
    def __init__(self, name: str, gui: QtWidgets.QWidget) -> None:
        super().__init__(gui)
        self.name = name
        self.server_socket: socket.socket
        self.multicast_socket: socket.socket
        self.port: int
        self.participants = []

    def serve(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", 0))  # Bind to a random available port
        self.port = self.server_socket.getsockname()[1]
        self.server_socket.listen(5)

        threading.Thread(target=self.broadcast_announcement).start()
        self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.heartbeat_check)
        self.heartbeat_timer.start()

        while True:
            peer_socket, address = self.server_socket.accept()
            print(f"Connection from {address} has been established.")
            self.participants.append((peer_socket, address))
            self.gui.add_peer(address[0], address[1])
            threading.Thread(target=self.listen_to_participant, args=(peer_socket,)).start()

    def broadcast_announcement(self):
        self.multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        info = AnnounceMessage(self.name, self.port)

        while True:
            msg = Message.from_bytes(self.multicast_socket.recv(BUFFER_SIZE))
            if msg.is_discovery():
                self.multicast_socket.sendto(info.encode(), (MCAST_GROUP, MCAST_PORT))

    def heartbeat_check(self):
        for participant in self.participants:
            try:
                participant[0].send(HeartbeatMessage(self.port).encode())
            except:
                self.participants.remove(participant)
                self.gui.remove_peer(participant[1][0])

    def listen_to_participant(self, peer_socket):
        while True:
            try:
                message = peer_socket.recv(BUFFER_SIZE)
                msg = Message.from_bytes(message)
                if msg.is_heartbeat():
                    continue
                print(message)
            except:
                self.participants.remove((peer_socket, peer_socket.getpeername()))
                self.gui.remove_peer(peer_socket.getpeername()[0])
                break


class Participant(Client):
    def __init__(self, name: str, gui: QtWidgets.QWidget) -> None:
        super().__init__(gui)
        self.name = name
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def listen(self):
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_socket.bind((MCAST_GROUP, MCAST_PORT))

        mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            msg = Message.from_bytes(multicast_socket.recv(BUFFER_SIZE))
            print(msg)
            if isinstance(msg, AnnounceMessage):
                self.gui.add_peer(msg.name, msg.port)

    def connect_to_host(self, host_ip: str, host_port: int):
        self.client_socket.connect((host_ip, host_port))

        join_msg = JoinMessage(self.name, self.client_socket.getsockname()[1])
        self.client_socket.send(join_msg.encode())

        def listen_to_host():
            while True:
                try:
                    message = self.client_socket.recv(BUFFER_SIZE)
                    print(message)
                except:
                    print("Connection to host lost.")
                    self.client_socket.close()
                    break

        listen_thread = threading.Thread(target=listen_to_host)
        listen_thread.start()

    def disconnect(self):
        self.client_socket.close()


class PeerLobby(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.client: Client

        self.peers = {}
        self.lock = threading.Lock()

    def initUI(self):
        self.setWindowTitle("Peer-to-Peer Lobby")
        self.setGeometry(100, 100, 400, 300)

        self.main_layout = QtWidgets.QVBoxLayout()

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.main_layout.addWidget(self.name_input)

        self.info_label = QtWidgets.QLabel("Select mode to start:")
        self.main_layout.addWidget(self.info_label)

        self.host_button = QtWidgets.QPushButton("Host")
        self.host_button.clicked.connect(self.start_host)
        self.main_layout.addWidget(self.host_button)

        self.join_button = QtWidgets.QPushButton("Join")
        self.join_button.clicked.connect(self.start_join)
        self.main_layout.addWidget(self.join_button)

        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_peers)
        self.main_layout.addWidget(self.refresh_button)
        self.refresh_button.setEnabled(False)

        self.peer_list_widget = QtWidgets.QListWidget()
        self.peer_list_widget.itemClicked.connect(self.list_clicked)
        self.main_layout.addWidget(self.peer_list_widget)

        self.setLayout(self.main_layout)

    def start_host(self):
        name = self.name_input.text()
        if not name:
            self.info_label.setText("Please enter your name.")
            return

        self.info_label.setText("Hosting...")
        self.host_button.setEnabled(False)
        self.join_button.setEnabled(False)
        self.refresh_button.setEnabled(True)

        self.client = Host(name, self)
        threading.Thread(target=self.client.serve).start()

    def start_join(self):
        name = self.name_input.text()
        if not name:
            self.info_label.setText("Please enter your name.")
            return

        self.info_label.setText("Joining...")
        self.host_button.setEnabled(False)
        self.join_button.setEnabled(False)
        self.refresh_button.setEnabled(True)

        self.client = Participant(name, self)
        threading.Thread(target=self.client.listen).start()

    def refresh_peers(self):
        self.client.refresh()

    def update_peer_list(self):
        self.peer_list_widget.clear()
        with self.lock:
            for peer_ip, (_, peer_port, _) in self.peers.items():
                self.peer_list_widget.addItem(f"{peer_ip}:{peer_port}")

    def add_peer(self, peer_ip, peer_port):
        with self.lock:
            self.peers[peer_ip] = (peer_ip, peer_port, time.time())
        self.update_peer_list()

    def remove_peer(self, peer_ip):
        with self.lock:
            del self.peers[peer_ip]
        self.update_peer_list()

    def list_clicked(self, item):
        if isinstance(self.client, Participant):
            peer_ip, peer_port = item.text().split(":")
            if isinstance(self.client, Host):
                self.client.participants.append((peer_ip, peer_port))
            else:
                self.client.connect_to_host(peer_ip, int(peer_port))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = PeerLobby()
    ex.show()
    sys.exit(app.exec_())
