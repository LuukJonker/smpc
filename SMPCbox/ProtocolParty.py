from typing import Type, Any
from SMPCbox.SMPCSocket import SMPCSocket
from SMPCbox.ProtocolStep import ProtocolStep

class ProtocolParty ():
    def __init__(self, name: str, address: str = None):
        self.__socket = SMPCSocket(name, address, is_listening_socket=True)
        self.__name = name
        self.__local_variables: dict[str, Any] = {}
        self.__protocol_steps: list[ProtocolStep] = []
    
    def get_socket (self) -> Type[SMPCSocket]:
        return self.__socket
    
    def get_party_name (self) -> str:
        return self.__name
    
    def print_local_variables(self):
        print(self.__local_variables)

    def set_local_variable(self, variable_name: str, value: Any):
        self.__local_variables[variable_name] = value
    

    def send_variable (self, receiver: Type['ProtocolParty'], variable_name: str):
        if not variable_name in self.__local_variables.keys():
            raise Exception(f"Trying to send unknown local variable \"{variable_name}\" from the party \"{self.get_party_name()}\"")
            
        self.__socket.send_variable(receiver, variable_name, self.__local_variables[variable_name])

    def receive_variable (self, sender: Type['ProtocolParty'], variable_name: str):
        self.__local_variables[variable_name] = self.__socket.receive_variable(sender, variable_name)
    
    def add_protocol_step(self, step_name: str = None):
        if step_name == None:
            step_name = f"step {len(self.__protocol_steps) + 1}"
        
        new_step = ProtocolStep(step_name)
        self.__protocol_steps.append(new_step)


    """ should be called to make sure the sockets exit nicely """
    def exit_protocol(self):
        self.__socket.close()