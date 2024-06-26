from __future__ import annotations
from typing import Any, TYPE_CHECKING, Union
import socket 
import threading
import json
import select
import time
from enum import Enum
from .exceptions import UnableToConnect

if TYPE_CHECKING:
    from ProtocolParty import ProtocolParty

class NotReceived:
    pass

"""
Parses an adress such as:
"127.0.0.1:3291"
and returns the tuple:
("127.0.0.1", 3291)
"""
def parse_address(address: str) -> tuple[str, int]:
    ip, port = address.split(":")
    return (ip, int(port))

def stringify_address(ip:str, port:int):
    return f"{ip}:{port}"

def get_key_by_value(d, value):
    for key, val in d.items():
        if val == value:
            return key
    return None

class MessageType(Enum):
    ANNOUNCE_NAME="ANNOUNCE"
    SEND_VARIABLES="SEND_VARS"

def parse_enum(enum_class, val):
    try:
        return enum_class(val)
    except ValueError as e:
        raise e

def construct_msg(type: MessageType, content: str) -> str:
    return f"{type.value}${len(content)}${content}"

class SMPCSocket ():
    def __init__ (self):
        self.ip = None
        self.port = None
        self.simulated = True

        # a buffer storing all received variables which have not been requested by the parrent class via
        # the receive variable function.
        # Behind each var a list is stored, this allows buffering of multiple values
        self.received_variables: dict[str | SMPCSocket, dict[str, list[Any]]] = {}
        self.smpc_socket_in_use = True
        self.client_sockets: dict[socket.socket, str | None] = {}
        self.listening_socket = None
        self.listening_thread = None
    
    def set_address(self, address: str):
        """
        Sets the address the party of this socket listens on.
        Calling this method sets the SMPCSocket to start using actual sockets
        """
        self.simulated = False
        self.ip, self.port = parse_address(address)

    def decode_received_msg(self, msg:str, sock: socket.socket):
        """ 
        decodes a message received from a client socket
        The message can be either variables or the initial msg that specifies who this client is
        by sending their listening ip and port.
        """
        
        
        msg_type, msg_length, rest = msg.split('$', maxsplit=2)
        msg_length = int(msg_length)
        msg_content = rest[:msg_length]
        additional_data = rest[msg_length:]

        msg_type = parse_enum(MessageType, msg_type)

        match msg_type:
            case MessageType.SEND_VARIABLES:
                variables = msg_content.split()
                var_names = []
                values = []
                for i in range(0, len(variables), 2):
                    var_name = variables[i]
                    value = json.loads(variables[i+1])
                    var_names.append(var_name)
                    values.append(value)
                
                sender_addr = self.client_sockets[sock]
                if sender_addr == None:
                    raise Exception("Received variables from unknown client socket")
                self.put_variables_in_buffer(sender_addr, var_names, values)
            
            case MessageType.ANNOUNCE_NAME:
                ip, port = parse_address(msg_content)
                self.client_sockets[sock] = stringify_address(ip,port)
            case _:
                raise Exception(f"Received message starting with unknown message type {msg_type}")
        
        if additional_data:
            # the data contained another message
            self.decode_received_msg(additional_data, sock)
    
    def start_listening(self):
        """
        Starts the listening thread of this socket.
        """
        # create the listening socket which will accept incomming connections and also read messages
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listening_socket.bind((self.ip, self.port))
        # TODO remove magic number for backlog in listen
        self.listening_socket.listen(5)
        self.listening_thread = threading.Thread(target=self.listen)
        self.listening_thread.start()
                
    def listen(self):
        if self.listening_socket is None:
            # listen only gets called from the start_listening method which inits the listening socket
            raise Exception()

        while self.smpc_socket_in_use:
            # TODO put the timeout as a setting (timeout needed so the socket stops if self.smpc_socket_in_use if false)
            client_socks = list(self.client_sockets.keys())
            readable_sockets, _, _ = select.select(client_socks + [self.listening_socket], [], [], 0.1)
            for socket in readable_sockets:
                if socket == self.listening_socket and self.smpc_socket_in_use:
                    client_socket, _ = self.listening_socket.accept()
                    # we do not yet know the listening ip and port this socket coresponds to
                    self.client_sockets[client_socket] = None
                else:
                    # TODO create a setting for buffer size
                    data = socket.recv(4096)
                    if data:
                        msg = data.decode()
                        self.decode_received_msg(msg, socket)
                    else:
                        pass
                        # The client has closed their side of the socket
       
        # close all the connections
        if not self.simulated and self.listening_socket:
            for connection in self.client_sockets.keys():
                connection.close()

        self.listening_socket.close()
    
    def get_address(self) -> tuple[str, int]:
        if self.ip == None or self.port == None:
            return "", 0
        
        return self.ip, self.port
    
    def connect_to_client(self, ip: str, port: int, timeout: float = 10):
        new_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start = time.time()
        while timeout == None or (time.time() - start) < timeout:
            try: 
                new_client.connect((ip, port))
                self.client_sockets[new_client] = stringify_address(ip, port)

                # announce who we are
                msg_content =  f"{self.ip}:{self.port}"
                message = construct_msg(MessageType.ANNOUNCE_NAME, msg_content)
                new_client.sendall(message.encode())
                return
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(0.25)
                continue
        
        # connection was unsucessfull
        raise UnableToConnect(ip, port)
                
        
    
    def connect_to_parties(self, other_parties: list[ProtocolParty], timeout=60):
        """
        Establishes a connection with all the provided SMPCSocket
        """
        if self.simulated:
            return
        
        # if we aren't simulated establish the connections
        for party in other_parties:
            ip, port = party.socket.get_address()
            if stringify_address(ip, port) not in self.client_sockets:
                self.connect_to_client(ip, port, timeout=timeout)
            
    
    """
    Closes the socket,
    Note that this doesn't allow the imediate reuse of the port. Since
    there is a TIME_WAIT untill the port is "released" (about 1-2 minutes)
    """
    def close(self):
        self.smpc_socket_in_use = False
        # wait on the listening thread to clean everything up
        if self.listening_thread is not None:
            self.listening_thread.join()
        

    def put_variables_in_buffer (self, sender: str | SMPCSocket, variable_names: list[str], values: list[Any]):
        if not sender in self.received_variables.keys():
            self.received_variables[sender] = {}
        
        # add all the provided variables
        for var, val in zip(variable_names, values):
            if var in self.received_variables[sender]:
                self.received_variables[sender][var].append(val)
            else:
                self.received_variables[sender][var] = [val]
    
    """
    Stores a received_variables in the buffer
    """
    def get_variable_from_buffer(self, sender: str | SMPCSocket, variable_name: str) -> Any:
        # check if this variable has been received from the specified sender
        if not (sender in self.received_variables.keys() and variable_name in self.received_variables[sender].keys()):
            return NotReceived()
        
        # get the value for the variable that arived first
        value = self.received_variables[sender][variable_name].pop(0)

        if len(self.received_variables[sender][variable_name]) == 0:
            del self.received_variables[sender][variable_name]
            
        return value
    

    """
    This function returns the variable received from the sender with the specified variable name.
    If this variable is not received from the sender then None is returned
    """
    def receive_variable(self, sender: 'ProtocolParty', variable_name: str, timeout: float = 10) -> Any:
        if self.simulated:
            value = self.get_variable_from_buffer(sender.socket, variable_name)
            return value
        else:
            # we keep checking untill the listening socket has put the message into the queue
            sender_addr = stringify_address(*sender.socket.get_address())

            start_time = time.time()
            while (time.time() - start_time < timeout):
                value = self.get_variable_from_buffer(sender_addr, variable_name)
                if not isinstance(value, NotReceived):
                    return value
                
                if self.ip == None:
                    # no need to wait for network delay since were simulating it all
                    break
                time.sleep(0.1)
            
            return NotReceived()

    """
    This function sends the variable to this socket. 
    """
    def send_variables (self, receiver: 'ProtocolParty', variable_names: list[str], values: list[Any]):
        receiver_socket: 'SMPCSocket' = receiver.socket
        if self.simulated:
              # we simulate the socket by putting the variable in the buffer of received variables
            receiver_socket.put_variables_in_buffer(self, variable_names, values)
        else: 
            # check for an existing connection
            addr = stringify_address(*receiver_socket.get_address())

            if addr not in self.client_sockets.values():
                raise Exception(f"Client with listening address {addr} not connected")
            
            msg = ""
            # Add all the variables
            for var, val in zip(variable_names, values):
                msg += f" {var} {json.dumps(val)}"

            msg = construct_msg(MessageType.SEND_VARIABLES, msg)
            socket = get_key_by_value(self.client_sockets, addr)
            if socket == None:
                # we have just checked that the addr exists so we know there will be a socket
                raise Exception()
            
            socket.sendall(msg.encode())
          
