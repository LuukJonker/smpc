from typing import Type, Any, Callable, Union
from SMPCbox.SMPCSocket import SMPCSocket

class ProtocolParty ():
    def __init__(self, name: str, address: str = None, is_listening_socket=True):
        """
        Instantiates a ProtocolParty. ProtocolParty instances are used within protocols, protocols themselfs
        instantiate ProtocolParty instances by default though when a user wants to assign a specific name
        to a certain party or wants to provide an address (ip:port) a party instance can also be provided
        to a protocol by using the set_protocol_parties or set_running_party methods of the protocol class.
        """
        self.__socket = SMPCSocket(name, address, is_listening_socket=is_listening_socket)
        self.__name = name
        self.__local_variables: dict[str, Any] = {}

        # a stack of prefixes which handle the namespaces of variable
        self.__namespace_prefixes: list[str] = []

    def get_namespace(self) -> str:
        if len(self.__namespace_prefixes) == 0:
            return ""
        
        # start with a '_' to seperate the var name from the namespace
        namespace = "_"
        for prefix in self.__namespace_prefixes:
            namespace = prefix + namespace
        return namespace
    
    def start_subroutine_protocol(self, subroutine_name: str):
        self.__namespace_prefixes.append(f"_{subroutine_name}")
    
    def end_subroutine_protocol(self):
        self.__namespace_prefixes.pop()

    def get_socket (self) -> Type[SMPCSocket]:
        return self.__socket
    
    def get_party_name (self) -> str:
        return self.__name
    
    def print_local_variables(self):
        print(self.__local_variables)
    
    def get_variable(self, variable_name: str):
        return self.__local_variables[self.get_namespace() + variable_name]

    def run_computation(self, computed_vars: Union[str, list[str]], input_vars: Union[str, list[str]], computation: Callable, description: str):
        # make sure the input vars and computed_vars are lists
        input_vars = [input_vars] if type(input_vars) == str else input_vars
        computed_vars = [computed_vars] if type(computed_vars) == str else computed_vars

        # get the input values
        input_vals = [self.get_variable(var) for var in input_vars]

        # add the namespace to the computed_var names
        computed_vars = [self.get_namespace() + name for name in computed_vars]

        # get the local variables
        res = computation(*input_vals)

        # assign the output if there is just a single output variable
        if len(computed_vars) == 1:
            self.__local_variables[computed_vars[0]] = res
            return
        
        # check if enough values are returned 
        if len(res) != len(computed_vars):
            raise Exception (f"The computation with description \"{description}\" returns {len(res)} output value(s), but is trying to assign to {len(computed_vars)} variable(s)!")
        
        # assign the values
        for i, var in enumerate(computed_vars):
            self.__local_variables[var] = res[i]

    def set_local_variable(self, variable_name: str, value: Any):
        self.__local_variables[self.get_namespace() + variable_name] = value

    def send_variable (self, receiver: Type['ProtocolParty'], variable_name: str):
        real_var_name = self.get_namespace() + variable_name
        if not real_var_name in self.__local_variables.keys():
            raise Exception(f"Trying to send unknown local variable \"{real_var_name}\" from the party \"{self.get_party_name()}\"")

        self.__socket.send_variable(receiver, real_var_name, self.get_variable(variable_name))

    def receive_variable (self, sender: Type['ProtocolParty'], variable_name: str):
        real_var_name = self.get_namespace() + variable_name
        self.__local_variables[real_var_name] = self.__socket.receive_variable(sender, real_var_name)

    """ should be called to make sure the sockets exit nicely """
    def exit_protocol(self):
        self.__socket.close()