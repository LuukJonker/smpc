from __future__ import annotations
from typing import Any, Callable, Union, TYPE_CHECKING
from .SMPCSocket import SMPCSocket, NotReceived
from .exceptions import NonExistentVariable, IncorrectComputationResultDimension, VariableNotReceived, InvalidLocalVariableAccess
import time
from sys import getsizeof

if TYPE_CHECKING:
    from ProtocolParty import TrackedStatistics


class TrackedStatistics():
    def __init__(self):
        self.execution_time: float = 0
        self.execution_CPU_time: float = 0
        self.wait_time: float = 0
        self.messages_send: int = 0
        self.messages_received: int = 0
        self.bytes_send: int = 0
        self.bytes_received: int = 0


    def __str__(self):
        return f"""
        Statistics
        execution_time: {self.execution_time}
        execution_CPU_time: {self.execution_CPU_time}
        wait_time: {self.wait_time}
        messages_send: {self.messages_send}
        bytes_send: {self.bytes_send}
        messages_received: {self.messages_received}
        bytes_received: {self.bytes_received}"""

    def __add__(self, other_stats: TrackedStatistics) -> TrackedStatistics:
        res = TrackedStatistics()
        res.execution_time = self.execution_time + other_stats.execution_time
        res.execution_CPU_time = self.execution_CPU_time + other_stats.execution_CPU_time
        res.wait_time = self.wait_time + other_stats.wait_time
        res.messages_send = self.messages_send + other_stats.messages_send
        res.messages_received = self.messages_received + other_stats.messages_received
        res.bytes_send = self.bytes_send + other_stats.bytes_send
        res.bytes_received = self.bytes_received + other_stats.bytes_received
        return res

class ProtocolParty ():
    def __init__(self, name: str):
        """
        Instantiates a ProtocolParty.
        """
        self.socket = SMPCSocket()
        self.__local_variables: dict[str, Any] = {}
        self.statistics = TrackedStatistics()
        self.name = name

        # a stack of prefixes which handle the namespaces of variable
        self.__namespace_prefixes: list[str] = []

        # stores the variables which have been "received" to not have to request them from the
        # SMPCSocket yet and the sender which send the variable
        self.not_yet_received_vars: dict[str, ProtocolParty] = {}

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
        old_prefix = self.__namespace_prefixes.pop()
        # we wait on any unreceived variables that were part of the subroutine
        # Not doing so can lead to weird behaviour since new unreceived variables if the protocol
        # is run again might think variables have already arived in the SMPCSocket otherwise
        unreceived_vars = []
        for var in self.not_yet_received_vars.keys():
            if var.startswith(old_prefix):
                unreceived_vars.append(var)
        
        for var in unreceived_vars:
            # retrieve the variable to flush it from the SMPCSocket
            self.get_variable(var)
    
    def print_local_variables(self):
        print(self.__local_variables)

    def __getitem__(self, key):
        # Allows to use [] to retrieve variables of a party.
        return self.get_variable(key)

    def is_local(self):
        return self.socket.simulated or self.socket.listening_socket is not None

    def get_variable(self, variable_name: str):
        if not self.is_local():
            raise InvalidLocalVariableAccess(self.name, variable_name)

        # handle the namespace
        variable_name = self.get_namespace() + variable_name

        # get the variable from the socket if this hasn't been done
        if variable_name in self.not_yet_received_vars.keys():
            sender = self.not_yet_received_vars[variable_name]
            # request the variable from the socket
            s_wait_time = time.perf_counter()
            value = self.socket.receive_variable(sender, variable_name)
            e_wait_time = time.perf_counter()
            if isinstance(value, NotReceived):
                raise VariableNotReceived(sender.name, variable_name)

            # add the received values bytes to the received bytes stat
            self.statistics.bytes_received += getsizeof(value)

            self.statistics.wait_time += e_wait_time - s_wait_time

            self.__local_variables[variable_name] = value
            # the variable has now been received
            del self.not_yet_received_vars[variable_name]

        if variable_name not in self.__local_variables.keys():
            raise NonExistentVariable(self.name, variable_name)

        return self.__local_variables[variable_name]

    def run_computation(self, computed_vars: Union[str, list[str]], computation: Callable, description: str):
        # make sure the computed_vars are a list
        computed_vars = [computed_vars] if type(computed_vars) == str else computed_vars

        # add the namespace to the computed_var names
        computed_vars = [self.get_namespace() + name for name in computed_vars]

        # get the local variables
        t_start = time.perf_counter()
        t_CPU_start = time.process_time()
        res = computation()
        t_CPU_end = time.process_time()
        t_end = time.perf_counter()
        self.statistics.execution_time += t_end - t_start
        self.statistics.execution_CPU_time += t_CPU_end - t_CPU_start

        # assign the output if there is just a single output variable
        if len(computed_vars) == 1:
            self.__local_variables[computed_vars[0]] = res
            return

        # check if enough values are returned
        if len(res) != len(computed_vars):
            IncorrectComputationResultDimension(description, res, len(computed_vars))

        # assign the values
        for i, var in enumerate(computed_vars):
            self.__local_variables[var] = res[i]

        return res

    def set_local_variable(self, variable_name: str, value: Any):
        self.__local_variables[self.get_namespace() + variable_name] = value

    def send_variables (self, receiver: 'ProtocolParty', variable_names: list[str]):
        values = [self.get_variable(var) for var in variable_names]

        # update the statistics
        self.statistics.messages_send += 1
        for i in values:
            self.statistics.bytes_send += getsizeof(i)

        variable_names = [self.get_namespace() + name for name in variable_names]
        self.socket.send_variables(receiver, variable_names, values)

    def receive_variables (self, sender: 'ProtocolParty', variable_names: list[str]):
        variable_names = [self.get_namespace() + name for name in variable_names]
        # add the variables to the not_yet_received_vars
        for name in variable_names:
            self.not_yet_received_vars[name] = sender

        self.statistics.messages_received += 1

    def get_statistics(self) -> TrackedStatistics:
        """
        Retreives the statistics of a single ProtocolParty
        """
        return self.statistics

    """ should be called to make sure the sockets exit nicely """
    def exit_protocol(self):
        self.socket.close()
