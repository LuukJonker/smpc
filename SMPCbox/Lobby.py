import sys
import socket
import threading
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import json
from typing import Any, Callable
from enum import Enum
import uuid
from SMPCbox.constants import (
    MAX_PORT,
    MCAST_GROUP,
    MCAST_PORT,
    BUFFER_SIZE,
    DISCOVERY_INTERVAL,
)


class MessageType(Enum):
    """Enum to get the type of message."""

    DISCOVERY = "DISCOVERY"
    ANNOUNCE = "ANNOUNCE"
    JOIN = "JOIN"
    MEMBERS = "MEMBERS"
    SETUP = "SETUP"
    READY = "READY"
    START = "START"


class Peer:
    """Class to store information about a peer."""

    def __init__(
        self, name: str, ip: str, port: int, uid: uuid.UUID | None = None
    ) -> None:
        self.uid = uid if uid else uuid.uuid1()
        self.name = name
        self.ip = ip
        self.port = port

    def encode(self) -> dict[str, Any]:
        """Encode a peer object to a dictionary.

        Returns:
            dict[str, Any]: The dictionary representation of the peer.
        """
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "uid": str(self.uid),
        }

    @classmethod
    def decode(cls, data: dict[str, Any]) -> "Peer":
        """Decode a dictionary to a peer object.

        Args:
            data (dict[str, Any]): The dictionary to decode.

        Returns:
            Peer: The peer object.
        """
        return Peer(data["name"], data["ip"], data["port"], uuid.UUID(data["uid"]))


class Message:
    """Class to represent a message."""

    def __init__(self, msg_type: MessageType, data: dict[str, Any]) -> None:
        self.msg_type = msg_type
        self.data = data

    def __repr__(self) -> str:
        return f"{self.msg_type.name}: {self.data}"

    def encode(self) -> bytes:
        """Encode the message to bytes.

        Returns:
            bytes: The encoded message.
        """
        data = self.data.copy()
        data["msg_type"] = self.msg_type.value
        return json.dumps(data).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Decode a message from bytes.

        Args:
            data (bytes): The bytes to decode.

        Raises:
            ValueError: If the message type is unknown.

        Returns:
            Message: The decoded message.
        """
        msg = json.loads(data.decode("utf-8"))
        msg_type = MessageType(msg["msg_type"])
        del msg["msg_type"]

        if msg_type == MessageType.DISCOVERY:
            return DiscoveryMessage()
        elif msg_type == MessageType.ANNOUNCE:
            return AnnounceMessage(msg["name"], msg["port"])
        elif msg_type == MessageType.JOIN:
            return JoinMessage(msg["name"], msg["port"])
        elif msg_type == MessageType.MEMBERS:
            return MemberMessage(msg["members"])
        elif msg_type == MessageType.SETUP:
            return SetupMessage(
                msg["protocol_name"],
                msg["party_name"],
                msg["addresses"],
                msg["configuration"],
            )
        elif msg_type == MessageType.READY:
            return ReadyMessage()
        elif msg_type == MessageType.START:
            return StartMessage()
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


class JoinMessage(Message):
    def __init__(self, name: str, port: int) -> None:
        super().__init__(MessageType.JOIN, {"name": name, "port": port})
        self.name = name
        self.port = port


class MemberMessage(Message):
    def __init__(self, members: list[dict]) -> None:
        super().__init__(MessageType.MEMBERS, {"members": members})
        self.members = members


class SetupMessage(Message):
    def __init__(
        self,
        protocol_name: str,
        party_name: str,
        addresses: dict[str, str],
        configuration: dict[str, Any],
    ) -> None:
        super().__init__(
            MessageType.SETUP,
            {
                "protocol_name": protocol_name,
                "party_name": party_name,
                "addresses": addresses,
                "configuration": configuration,
            },
        )
        self.protocol_name = protocol_name
        self.party_name = party_name
        self.addresses = addresses
        self.configuration = configuration


class ReadyMessage(Message):
    def __init__(self) -> None:
        super().__init__(MessageType.READY, {})


class StartMessage(Message):
    def __init__(self) -> None:
        super().__init__(MessageType.START, {})


class Client:
    """Base class for the host and participant clients."""

    def __init__(self, gui: "PeerLobby", setup_distributed_protocol: Callable) -> None:
        self.gui = gui
        self.running = True
        self.uid = uuid.uuid1()
        self.setup_distributed_protocol = setup_distributed_protocol

    def send_ready(self):
        pass

    def stop(self):
        """Stop the client."""
        self.running = False


class Host(Client):
    def __init__(
        self, name: str, gui: QtWidgets.QWidget, setup_distributed_protocol: Callable
    ) -> None:
        super().__init__(gui, setup_distributed_protocol)
        self.name = name
        self.server_socket: socket.socket
        self.multicast_socket: socket.socket
        self.port: int
        self.participants: list[Peer] = []
        self.participant_sockets: dict[uuid.UUID, socket.socket] = {}
        self.ready_participants: dict[uuid.UUID, bool] = {}

    def serve(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", 0))  # Bind to a random available port
        self.port = self.server_socket.getsockname()[1]
        self.server_socket.listen(5)

        threading.Thread(target=self.broadcast_announcement).start()

        while self.running:
            try:
                self.server_socket.settimeout(1)
                peer_socket, address = self.server_socket.accept()
                threading.Thread(
                    target=self.listen_to_participant, args=(peer_socket, address)
                ).start()
            except socket.timeout:
                continue

        self.server_socket.close()

    def broadcast_announcement(self):
        self.multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_socket.bind(("", MCAST_PORT))

        mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
        self.multicast_socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq
        )

        info = AnnounceMessage(self.name, self.port)

        while self.running:
            try:
                self.multicast_socket.settimeout(1)
                msg = Message.from_bytes(self.multicast_socket.recv(BUFFER_SIZE))
                print("Host received:", msg)
                if isinstance(msg, DiscoveryMessage):
                    print("Host sending:", info)
                    self.multicast_socket.sendto(
                        info.encode(), (MCAST_GROUP, MCAST_PORT)
                    )
            except socket.timeout:
                continue

        self.multicast_socket.close()

    def listen_to_participant(self, peer_socket: socket.socket, address):
        join_message = Message.from_bytes(peer_socket.recv(BUFFER_SIZE))
        if not isinstance(join_message, JoinMessage):
            peer_socket.close()
            return

        peer = Peer(join_message.name, address[0], join_message.port)
        self.participant_sockets[peer.uid] = peer_socket

        self.participants.append(peer)

        self.gui.add_peer(peer)

        peer_socket.send(
            MemberMessage([p.encode() for p in self.participants]).encode()
        )

        while self.running:
            try:
                peer_socket.settimeout(1)
                message = peer_socket.recv(BUFFER_SIZE)
                if not message:
                    print("Connection to participant lost.")
                    self.participants.remove(peer)
                    self.gui.remove_peer(peer.uid)
                    break
                msg = Message.from_bytes(message)

                if isinstance(msg, ReadyMessage):
                    self.ready_participants[peer.uid] = True

                    if all(self.ready_participants.values()):
                        self.send_start()
                        self.gui.start_signal.emit()
            except socket.timeout:
                continue
            except:
                print("Connection to participant lost.")
                self.participants.remove(peer)
                self.gui.remove_peer(peer.uid)
                break
        peer_socket.close()

    def send_configuration(
        self,
        protocol_name: str,
        configuration: dict[str, Any],
        mapping: dict[str, Peer],
    ):
        self.ready_participants = {v.uid: False for v in mapping.values()}

        reverse_mapping = {v.uid: k for k, v in mapping.items()}

        addresses = {
            k: f"{v.ip}:{MAX_PORT - i}" for i, (k, v) in enumerate(mapping.items())
        }

        for participant in self.participants:
            party_name = reverse_mapping[participant.uid]
            participant_socket = self.participant_sockets[participant.uid]
            participant_socket.send(
                SetupMessage(
                    protocol_name, party_name, addresses, configuration
                ).encode()
            )

        self.setup_distributed_protocol(
            protocol_name, reverse_mapping[self.uid], addresses, configuration
        )

    def send_ready(self):
        self.ready_participants[self.uid] = True

        if all(self.ready_participants.values()):
            self.send_start()
            self.gui.start_signal.emit()

    def send_start(self):
        for participant in self.participants:
            participant_socket = self.participant_sockets[participant.uid]
            participant_socket.send(StartMessage().encode())


class Participant(Client):
    def __init__(
        self, name: str, gui: "PeerLobby", setup_distributed_protocol: Callable
    ) -> None:
        super().__init__(gui, setup_distributed_protocol)
        self.name = name
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.joined = False

    def refresh(self):
        self.gui.set_peers([])
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        multicast_socket.sendto(DiscoveryMessage().encode(), (MCAST_GROUP, MCAST_PORT))
        multicast_socket.close()

    def listen(self):
        multicast_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_socket.bind(("", MCAST_PORT))

        mreq = socket.inet_aton(MCAST_GROUP) + socket.inet_aton("0.0.0.0")
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while self.running and not self.joined:
            try:
                multicast_socket.settimeout(1)
                msg_bytes, address = multicast_socket.recvfrom(BUFFER_SIZE)
                msg = Message.from_bytes(msg_bytes)
                if isinstance(msg, AnnounceMessage) and not self.joined:
                    self.gui.add_peer(Peer(msg.name, address[0], msg.port))
            except socket.timeout:
                continue

        multicast_socket.close()

    def connect_to_host(self, peer: Peer):
        if self.joined:
            self.leave_current_room()

        host_ip = peer.ip
        host_port = peer.port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((host_ip, host_port))
        except Exception:
            self.gui.remove_peer(peer.uid)
            return

        join_msg = JoinMessage(self.name, self.client_socket.getsockname()[1])
        self.client_socket.send(join_msg.encode())
        self.joined = True
        self.current_host = (host_ip, host_port)

        threading.Thread(target=self.listen_to_host).start()

    def listen_to_host(self):
        while self.running and self.joined:
            try:
                self.client_socket.settimeout(1)
                message = self.client_socket.recv(BUFFER_SIZE)
                if not message:
                    print("Connection to host lost.")
                    self.leave_current_room()
                    break

                decoded = Message.from_bytes(message)
                if isinstance(decoded, MemberMessage):
                    members = [Peer.decode(m) for m in decoded.members]
                    self.gui.set_peers(members)

                if isinstance(decoded, SetupMessage):
                    self.setup_distributed_protocol(
                        decoded.protocol_name,
                        decoded.party_name,
                        decoded.addresses,
                        decoded.configuration,
                    )

                if isinstance(decoded, StartMessage):
                    self.gui.start_signal.emit()

            except socket.timeout:
                continue
            except Exception as e:
                print("Connection to host lost.", e)
                self.leave_current_room()
                break

    def send_ready(self):
        self.client_socket.send(ReadyMessage().encode())

    def leave_current_room(self):
        if self.joined:
            self.client_socket.close()
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.joined = False
            self.current_host = None
            self.gui.on_leave_room()

    def disconnect(self):
        self.running = False
        self.leave_current_room()


class ListItem(QtWidgets.QListWidgetItem):
    def __init__(self, peer: Peer):
        super().__init__(peer.name)
        self.peer = peer


class PeerLobby(QtWidgets.QMainWindow):
    setup_signal = pyqtSignal(str)
    start_signal = pyqtSignal()

    def __init__(
        self,
        on_role_selcection: Callable[[str], None],
        on_host_start: Callable,
        setup_distributed_protocol: Callable,
    ):
        super().__init__()

        self.on_role_selcection = on_role_selcection
        self.on_host_start = on_host_start
        self.setup = setup_distributed_protocol

        self.initUI()
        self.client: Client
        self.peers: dict[uuid.UUID, Peer] = {}
        self.lock = threading.Lock()
        self.discovery_timer = threading.Timer(DISCOVERY_INTERVAL, self.discovery)
        self.discovery_timer.start()

    def initUI(self):
        self.setWindowTitle("Peer-to-Peer Lobby")
        self.setGeometry(100, 100, 500, 400)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Name input
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Your Name:"))
        self.name_input = QtWidgets.QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.host_button = QtWidgets.QPushButton("Host Room")
        self.host_button.clicked.connect(self.start_host)
        button_layout.addWidget(self.host_button)

        self.join_button = QtWidgets.QPushButton("Join as Participant")
        self.join_button.clicked.connect(self.start_participant)
        button_layout.addWidget(self.join_button)

        layout.addLayout(button_layout)

        self.horizontal_line = QtWidgets.QFrame()
        self.horizontal_line.setFrameShape(QtWidgets.QFrame.HLine)
        self.horizontal_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(self.horizontal_line)

        self.info_label = QtWidgets.QLabel("")
        layout.addWidget(self.info_label)

        self.peer_list_widget = QtWidgets.QListWidget()
        self.peer_list_widget.itemClicked.connect(self.list_clicked)
        layout.addWidget(self.peer_list_widget)

        self.action_button = QtWidgets.QPushButton("")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.on_action_button_click)
        layout.addWidget(self.action_button)

    def set_status(self, status: str):
        statusbar = self.statusBar()
        if statusbar:
            statusbar.showMessage(status)

    def start_host(self):
        name = self.name_input.text()
        if not name:
            self.info_label.setText("Please enter your name.")
            return

        self.on_role_selcection("host")

        self.set_status("Starting host...")
        self.info_label.setText(f"{name}'s room")
        self.host_button.setEnabled(False)
        self.join_button.setEnabled(False)

        self.action_button.setText("Start")
        self.action_button.setEnabled(True)

        self.client = Host(name, self, self.setup)
        threading.Thread(target=self.client.serve).start()

    def start_participant(self):
        name = self.name_input.text()
        if not name:
            self.info_label.setText("Please enter your name.")
            return

        self.on_role_selcection("participant")

        self.set_status("Joining room...")
        self.info_label.setText("Select a room to join.")
        self.host_button.setEnabled(False)
        self.join_button.setEnabled(False)

        self.action_button.setText("Refresh")
        self.action_button.setEnabled(True)

        self.client = Participant(name, self, self.setup)
        threading.Thread(target=self.client.listen).start()

    def on_action_button_click(self):
        if isinstance(self.client, Host):
            self.start_protocol()
        elif isinstance(self.client, Participant):
            if self.client.joined:
                self.leave_room()
            else:
                self.refresh_peers()

    def start_protocol(self):
        # Implement the protocol start logic here
        self.action_button.setEnabled(False)
        self.set_status("Protocol started")

        self.on_host_start()

    def on_close_protocol(self):
        self.set_status("Protocol ended")
        self.action_button.setEnabled(True)

    def leave_room(self):
        if isinstance(self.client, Participant):
            self.client.leave_current_room()

    def on_leave_room(self):
        if not isinstance(self.client, Participant):
            return

        self.set_status("Left the room")
        self.info_label.setText("Select a room to join.")
        self.action_button.setText("Refresh")
        threading.Thread(target=self.client.listen).start()
        self.set_peers([])
        self.refresh_peers()
        self.update_peer_list()

    def refresh_peers(self):
        if isinstance(self.client, Participant):
            self.client.refresh()

    def discovery(self):
        if hasattr(self, "client") and isinstance(self.client, Participant):
            self.client.refresh()

    def get_host(self):
        if not isinstance(self.client, Host):
            raise ValueError("Client is not a host.")

        return Peer(
            self.client.name,
            self.client.server_socket.getsockname()[0],
            self.client.port,
            uid=self.client.uid,
        )

    def update_peer_list(self):
        self.peer_list_widget.clear()
        with self.lock:
            for peer in self.peers.values():
                self.peer_list_widget.addItem(ListItem(peer))

    def set_peers(self, peers: list[Peer]):
        dict_peers = {peer.uid: peer for peer in peers}
        with self.lock:
            self.peers = dict_peers
        self.update_peer_list()

    def add_peer(self, peer: Peer):
        with self.lock:
            self.peers[peer.uid] = peer
        self.update_peer_list()

    def remove_peer(self, uid: uuid.UUID):
        with self.lock:
            for key in list(self.peers.keys()):
                if key == uid:
                    del self.peers[key]
        self.update_peer_list()

    def list_clicked(self, item: ListItem):
        if isinstance(self.client, Participant) and not self.client.joined:
            print(f"Connecting to {item.text()}")
            self.info_label.setText(f"{item.text()}'s room")
            self.client.connect_to_host(item.peer)
            self.action_button.setText("Leave")

    def closeEvent(self, a0):
        if hasattr(self, "client") and self.client:
            self.client.stop()
        self.discovery_timer.cancel()

        super().closeEvent(a0)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = PeerLobby(
        lambda role: print(role),
        lambda: print("Host started"),
        lambda *args, **kwargs: print(args, kwargs),
    )
    ex.show()
    sys.exit(app.exec_())
