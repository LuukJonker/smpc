import sys
import socket
import threading
import time
from PyQt5 import QtWidgets
import json
from typing import Any, Dict, Tuple
from enum import Enum

MCAST_GROUP = "224.1.1.1"
MCAST_PORT = 5007
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 5  # seconds
DISCOVERY_INTERVAL = 5  # seconds
TIMEOUT_INTERVAL = 15  # seconds


class MessageType(Enum):
    DISCOVERY = "DISCOVERY"
    ANNOUNCE = "ANNOUNCE"
    HEARTBEAT = "HEARTBEAT"
    JOIN = "JOIN"
    MEMBERS = "MEMBERS"

class Message:
    def __init__(self, msg_type: MessageType, data: Dict[str, Any]) -> None:
        self.msg_type = msg_type
        self.data = data

    def __repr__(self) -> str:
        return f"{self.msg_type.name}: {self.data}"

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
        elif msg_type == MessageType.MEMBERS:
            return MemberMessage(msg["members"])
        else:
            raise ValueError(f"Unknown message type: {msg_type}")

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

class MemberMessage(Message):
    def __init__(self, members: list[tuple]) -> None:
        super().__init__(MessageType.MEMBERS, {"members": members})
        self.members = members

class Client:
    def __init__(self, gui: QtWidgets.QWidget) -> None:
        self.gui = gui
        self.running = True

    def refresh(self):
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        multicast_socket.sendto(DiscoveryMessage().encode(), (MCAST_GROUP, MCAST_PORT))
        multicast_socket.close()

    def stop(self):
        self.running = False

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
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", 0))  # Bind to a random available port
        self.port = self.server_socket.getsockname()[1]
        self.server_socket.listen(5)

        threading.Thread(target=self.broadcast_announcement).start()
        self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.heartbeat_check)
        self.heartbeat_timer.start()

        while self.running:
            try:
                self.server_socket.settimeout(1)
                peer_socket, address = self.server_socket.accept()
                threading.Thread(target=self.listen_to_participant, args=(peer_socket, address)).start()
            except socket.timeout:
                continue

        self.server_socket.close()

    def broadcast_announcement(self):
        self.multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_socket.bind(('', MCAST_PORT))

        mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        info = AnnounceMessage(self.name, self.port)

        while self.running:
            try:
                self.multicast_socket.settimeout(1)
                msg = Message.from_bytes(self.multicast_socket.recv(BUFFER_SIZE))
                print("Host received:", msg)
                if isinstance(msg, DiscoveryMessage):
                    print("Host sending:", info)
                    self.multicast_socket.sendto(info.encode(), (MCAST_GROUP, MCAST_PORT))
            except socket.timeout:
                continue

        self.multicast_socket.close()

    def heartbeat_check(self):
        if not self.running:
            return
        for participant in self.participants:
            try:
                participant[0].send(HeartbeatMessage(self.port).encode())
            except:
                self.participants.remove(participant)
                self.gui.remove_peer(participant[1][0])
        self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.heartbeat_check)
        self.heartbeat_timer.start()

    def listen_to_participant(self, peer_socket: socket.socket, address):
        join_message = Message.from_bytes(peer_socket.recv(BUFFER_SIZE))
        if not isinstance(join_message, JoinMessage):
            peer_socket.close()
            return

        self.participants.append((peer_socket, join_message.name, address))

        self.gui.add_peer(join_message.name, address[0], join_message.port)

        peer_socket.send(MemberMessage([(p[1], p[2]) for p in self.participants]).encode())

        while self.running:
            try:
                peer_socket.settimeout(1)
                message = peer_socket.recv(BUFFER_SIZE)
                if not message:
                    break
                msg = Message.from_bytes(message)
                if isinstance(msg, HeartbeatMessage):
                    continue
                print(message)
            except socket.timeout:
                continue
            except:
                self.participants.remove((peer_socket, peer_socket.getpeername()))
                self.gui.remove_peer(peer_socket.getpeername()[0])
                break
        peer_socket.close()

class Participant(Client):
    def __init__(self, name: str, gui: QtWidgets.QWidget) -> None:
        super().__init__(gui)
        self.name = name
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.joined = False

    def listen(self):
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_socket.bind(('', MCAST_PORT))

        mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while self.running:
            try:
                multicast_socket.settimeout(1)
                msg_bytes, address = multicast_socket.recvfrom(BUFFER_SIZE)
                msg = Message.from_bytes(msg_bytes)
                print(msg)
                if isinstance(msg, AnnounceMessage):
                    self.gui.add_peer(msg.name, address[0], msg.port)
            except socket.timeout:
                continue

        multicast_socket.close()

    def connect_to_host(self, host_ip: str, host_port: int):
        self.client_socket.connect((host_ip, host_port))

        join_msg = JoinMessage(self.name, self.client_socket.getsockname()[1])
        self.client_socket.send(join_msg.encode())

        def listen_to_host():
            while self.running:
                try:
                    self.client_socket.settimeout(1)
                    message = self.client_socket.recv(BUFFER_SIZE)
                    if not message:
                        break

                    decoded = Message.from_bytes(message)
                    if isinstance(decoded, MemberMessage):
                        members = decoded.members
                        self.gui.set_peers(members)

                    print(message)
                except socket.timeout:
                    continue
                except Exception as e:
                    print("Connection to host lost.", e)
                    self.client_socket.close()
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    break

        listen_thread = threading.Thread(target=listen_to_host)
        listen_thread.start()

    def disconnect(self):
        self.running = False
        self.client_socket.close()

class ListItem(QtWidgets.QListWidgetItem):
    def __init__(self, name: str, ip: str, port: int):
        super().__init__(name)
        self.ip = ip
        self.port = port

class PeerLobby(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.client: Client
        self.peers: dict[tuple[str, int], str] = {}
        self.lock = threading.Lock()
        self.discovery_timer = threading.Timer(DISCOVERY_INTERVAL, self.discovery)
        self.discovery_timer.start()

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

    def discovery(self):
        if hasattr(self, 'client') and isinstance(self.client, Participant):
            self.client.refresh()

    def update_peer_list(self):
        self.peer_list_widget.clear()
        with self.lock:
            for (host_ip, host_port), host_name in self.peers.items():
                self.peer_list_widget.addItem(ListItem(host_name, host_ip, host_port))

    def set_peers(self, peers: list[tuple]):
        dict_peers = {(address[0], address[1]): name for name, address in peers}
        with self.lock:
            self.peers = dict_peers
        self.update_peer_list()

    def add_peer(self, host_name: str, host_ip: str, host_port: int):
        with self.lock:
            self.peers[(host_ip, host_port)] = host_name
        self.update_peer_list()

    def remove_peer(self, host_ip):
        with self.lock:
            for key in list(self.peers.keys()):
                if key[0] == host_ip:
                    del self.peers[key]
        self.update_peer_list()

    def list_clicked(self, item: ListItem):
        if isinstance(self.client, Participant):
            print(f"Connecting to {item.text()}")
            self.client.connect_to_host(item.ip, item.port)

    def closeEvent(self, a0):
        if hasattr(self, 'client') and self.client:
            self.client.stop()
        self.discovery_timer.cancel()

        super().closeEvent(a0)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = PeerLobby()
    ex.show()
    sys.exit(app.exec_())
