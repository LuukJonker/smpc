from typing import Any, Type
import socket 
import threading
import json

"""
Parses an adress such as:
"127.0.0.1:3291"
and returns the tuple:
("127.0.0.1", 3291)
"""
def parse_address(address: str) -> tuple[str, int]:
    ip, port = address.split(":")
    return (ip, int(port))

class SMPCSocket ():
    def __init__ (self, address: str = None):
        self.address = address
        # a buffer storing all received variables which have not been requested by the parrent class via
        # the receive variable function
        self.received_variables: dict[Type['SMPCSocket'], dict[str, Any]] = {}
        self.listening_socket = None

        if address:
            # Create a socket which connects to the specified address.
            pass
    
    def get_address(self) -> str:
        return self.address
    
    def put_variable_in_buffer (self, sender: Type['SMPCSocket'], variable_name: str, value: Any):
        if not sender in self.received_variables.keys():
            self.received_variables[sender] = {}

        self.received_variables[sender][variable_name] = value
    
    """
    Stores a received_variables in the buffer
    """
    def get_variable_from_buffer(self, sender: Type['SMPCSocket'], variable_name: str) -> Any:
        # check if this variable has been received from the specified sender
        if not (sender in self.received_variables.keys() and variable_name in self.received_variables[sender].keys()):
            return None
        
        value = self.received_variables[sender][variable_name]
        del self.received_variables[sender][variable_name]
        return value
    

    """
    This function returns the variable received from the sender with the specified variable name.
    If this variable is not received from the sender then an Exception is raised.
    """
    def receive_variable(self, sender: Type['ProtocolParty'], variable_name: str, timeout: float = 1) -> Any:
        if self.listening_socket:
            pass
        else:
            sender_socket: Type['SMPCSocket'] = sender.get_socket()
            value = self.get_variable_from_buffer(sender_socket, variable_name)
            if value == None:
                raise Exception(f"The variable \"{variable_name}\" has not been received from the party \"{sender.get_party_name()}\"\n Make sure the send_variable is called before receive_variable.")
            return value
            
    """
    This function sends the variable to this socket. 
    """
    def send_variable (self, receiver: Type['ProtocolParty'], variable_name: str, value: Any):
        receiver_socket: Type['SMPCSocket'] = receiver.get_socket()
        if self.listening_socket:
            pass
        else: 
            # we simulate the socket by putting the variable in the buffer of received variables
            receiver_socket.put_variable_in_buffer(self, variable_name, value)
