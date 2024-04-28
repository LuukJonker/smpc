"""
This file defines all the datastructures which store the opperations being performed.
All the opperations are inherited versions of the ProtocolOpperation class.
"""

from enum import Enum
from abc import ABC
from SMPCbox.ProtocolParty import ProtocolParty
from typing import Any, Type

class ProtocolOpperation(ABC):
    pass

class LocalComputation(ProtocolOpperation):
    def __init__(self, party: ProtocolParty, computed_variables: dict[str, Any], computation_description: str):
        self.party = party
        self.computed_variables = computed_variables
        self.description = computation_description
    
    def get_description(self) -> str:
        var_string = ", ".join(self.computed_variables)
        return f"{var_string} = {self.description}"
    
    def __str__(self) -> str:
        return f"{self.party}: {self.get_description()}"

class SendVariables(ProtocolOpperation):
    def __init__(self, sender: ProtocolParty, receiver: ProtocolParty, variables: dict[str, Any]):
        self.sender = sender.name
        self.receiver = receiver.name
        self.send_variables = variables
    
    def __str__(self) -> str:
        return f"{self.party}: send {self.send_variables} to {self.receiver}"
    
class AnnounceGlobals(ProtocolOpperation):
    def __init__(self, announcer: ProtocolParty, variables: dict[str, Any]):
        self.announcer = announcer.name
        self.announced_variables = variables
    
    def __str__(self) -> str:
        return f"{self.party}: announce {self.announced_variables}"
    
class ProtocolSubroutine(ProtocolOpperation):
    """
    A special type of ProtocolOpperation which is used when a protocol is used as a subroutine.
    The role_assignment contains a mapping from the protocol roles to the protocol party name
    The input_variable_mapping contains, for each role, a mapping of the input variable name as mentioned
    in the subroutine to the corresponding local variable name used in the ProtocolParty
    """
    def __init__(self, subroutine_protocol: Type['AbstractProtocol'], role_assignment: dict[str, str], input_variable_mapping: dict[str, dict[str, str]], output_variable_mapping: dict[str, dict[str, str]]):
        self.step_description: list[Type['ProtocolStep']] = subroutine_protocol.protocol_steps
        self.role_assignment = role_assignment
        self.input_variables = input_variable_mapping
        self.output_variables = output_variable_mapping

