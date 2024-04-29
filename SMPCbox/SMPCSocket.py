from typing import Any, Type
import socket 
import threading
import json
import select
import time

"""
Parses an adress such as:
"127.0.0.1:3291"
and returns the tuple:
("127.0.0.1", 3291)
"""
def parse_address(address: str) -> tuple[str, int]:
    if address == None:
        return (None, None)
    ip, port = address.split(":")
    return (ip, int(port))

class SMPCSocket ():
    def __init__ (self, party_name:str, address: str = None, is_listening_socket:bool=False):
        self.ip, self.port = parse_address(address)
        self.name = party_name
        # a buffer storing all received variables which have not been requested by the parrent class via
        # the receive variable function
        self.received_variables: dict[str, dict[str, Any]] = {}
        self.listening_socket = None

        self.smpc_socket_in_use = True
        self.client_sockets = []
        self.listening_thread = None

        if self.ip:
            if is_listening_socket:
                # create the listening socket which will accept incomming connections and also read messages
                self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print("LISTEN ON", self.ip, self.port)
                self.listening_socket.bind((self.ip, self.port))
                # TODO remove magic number for backlog in listen
                self.listening_socket.listen(5)
                self.listening_thread = threading.Thread(target=self.listen_for_connections)
                self.listening_thread.start()
        

                
    def listen_for_connections(self):
        while self.smpc_socket_in_use:
            # TODO put the timeout as a setting (timeout needed so the socket stops if self.smpc_socket_in_use if false)
            readable_sockets, _, _ = select.select(self.client_sockets + [self.listening_socket], [], [], 0.1)
            for socket in readable_sockets:
                if socket == self.listening_socket and self.smpc_socket_in_use:
                    client_socket, client_address = self.listening_socket.accept()
                    self.client_sockets.append(client_socket)
                else:
                    # TODO create a setting for buffer size
                    data = socket.recv(4096)
                    if data:
                        sender_name, *variables = data.decode().split()

                        var_names = []
                        values = []
                        for i in range(0, len(variables), 2):
                            var_name = variables[i]
                            value = json.loads(variables[i+1])

                            var_names.append(var_name)
                            values.append(value)

                        self.put_variables_in_buffer(sender_name, var_names, values)
                    else:
                        socket.close()
                        self.client_sockets.remove(socket)
    
    def get_address(self):
        return self.ip, self.port
    
    """
    Closes the socket,
    Note that this doesn't allow the imediate reuse of the port. Since
    there is a TIME_WAIT untill the port is "released" (about 1-2 minutes)
    """
    def close(self):
        self.smpc_socket_in_use = False
        if self.ip:
            if self.listening_socket:
                self.listening_thread.join()
                self.listening_socket.close()
                for connection in self.client_sockets:
                    connection.close()


    """
    This method is used to find a client from the list of already existing connections.
    """
    def find_client_with_address(self, ip, port):
        for client in self.client_sockets:
            client_ip, client_port = client.getsockname()
            if client_ip == ip and client_port == port:
                return client
        return None
        

    def put_variables_in_buffer (self, sender_name: str, variable_names: list[str], values: list[Any]):
        if not sender_name in self.received_variables.keys():
            self.received_variables[sender_name] = {}
        
        # add all the provided variables
        for var, val in zip(variable_names, values):
            self.received_variables[sender_name][var] = val
    
    """
    Stores a received_variables in the buffer
    """
    def get_variable_from_buffer(self, sender_name: str, variable_name: str) -> Any:
        # check if this variable has been received from the specified sender
        if not (sender_name in self.received_variables.keys() and variable_name in self.received_variables[sender_name].keys()):
            return None
        
        value = self.received_variables[sender_name][variable_name]
        del self.received_variables[sender_name][variable_name]
        return value
    

    """
    This function returns the variable received from the sender with the specified variable name.
    If this variable is not received from the sender then an Exception is raised.
    """
    def receive_variable(self, sender: Type['Protocolc80Party'], variable_name: str, timeout: float = 10) -> Any:
        if self.ip:
            # we keep checking untill the listening socket has put the message into the queue
            start_time = time.time()
            while (time.time() - start_time < timeout):
                value = self.get_variable_from_buffer(sender.name, variable_name)
                if value != None:
                    return value
                
                if self.ip == None:
                    # no need to wait for network delay since were simulating it all
                    break
                time.sleep(0.1)
    
            raise Exception(f"The variable \"{variable_name}\" has not been received from the party \"{sender.name}\"")
        else:
            value = self.get_variable_from_buffer(sender.name, variable_name)
            if value == None:
                raise Exception(f"The variable \"{variable_name}\" has not been received from the party \"{sender.name}\"")
            return value

    """
    This function sends the variable to this socket. 
    """
    def send_variables (self, receiver: Type['ProtocolParty'], variable_names: list[str], values: list[Any]):
        receiver_socket: Type['SMPCSocket'] = receiver.socket
        if self.ip:
            # check for an existing connection
            dest_ip, dest_port = receiver_socket.get_address()
            existing_socket: Type[socket.socket] = self.find_client_with_address(dest_ip, dest_port)

            if existing_socket == None:
                # no connection so create a new connection
                new_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new_client.connect((dest_ip, dest_port))
                self.client_sockets.append(new_client)
                existing_socket = new_client
            
            # send the message
            msg = f"{self.name}"

            # Add all the variables
            for var, val in zip(variable_names, values):
                msg += f" {var} {json.dumps(val)}"

            existing_socket.sendall(msg.encode())
        else: 
            # we simulate the socket by putting the variable in the buffer of received variables
            receiver_socket.put_variables_in_buffer(self.name, variable_names, values)
