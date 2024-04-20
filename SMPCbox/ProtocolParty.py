from typing import Type, Any, Callable, Union
from SMPCbox.SMPCSocket import SMPCSocket
from SMPCbox.ProtocolStep import ProtocolStep

class ProtocolParty ():
    def __init__(self, name: str, address: str = None):
        self.__socket = SMPCSocket(name, address, is_listening_socket=True)
        self.__name = name
        self.__local_variables: dict[str, Any] = {}
        self.__steps: list[ProtocolStep] = []

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

        if (len(self.__steps) == 0): raise Exception ("No protocol step defined before adding a computation. Use the add_protocol_step method before adding computations.")

        # add the namespace to the computed_var names
        computed_vars = [self.get_namespace() + name for name in computed_vars]
        self.__steps[-1].run_computation(computed_vars, input_vals, computation, self.__local_variables, description)

    def set_local_variable(self, variable_name: str, value: Any):
        self.__local_variables[self.get_namespace() + variable_name] = value

    def send_variable (self, receiver: Type['ProtocolParty'], variable_name: str):
        if not variable_name in self.__local_variables.keys():
            raise Exception(f"Trying to send unknown local variable \"{variable_name}\" from the party \"{self.get_party_name()}\"")
            
        self.__socket.send_variable(receiver, variable_name, self.get_variable(variable_name))

    def receive_variable (self, sender: Type['ProtocolParty'], variable_name: str):
        real_var_name = self.get_namespace() + variable_name
        self.__local_variables[real_var_name] = self.__socket.receive_variable(sender, real_var_name)
    
    def add_protocol_step(self, step_name: str = None):
        if step_name == None:
            step_name = f"step {len(self.__protocol_steps) + 1}"
        
        self.__steps.append(ProtocolStep(step_name))

    """ should be called to make sure the sockets exit nicely """
    def exit_protocol(self):
        self.__socket.close()