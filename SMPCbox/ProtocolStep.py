from SMPCbox.ProtocolOpps import ProtocolOpperation
from abc import ABC
from typing import Type

class ProtocolStep(ABC):
    """
    This class is used to 'store' the opperations performed within a step.
    The class simpily stores the name of the step and a list of ProtocolOpperations
    """
    def __init__(self, name: str):
        self.step_name = name
        self.step_description: list[ProtocolOpperation] = []
        
    def add_opperation (self, opp: ProtocolOpperation):
        self.step_description.append(opp)
    
    def remove_last_opperation (self):
        """
        Can be used to remove opperations added by methods which are used as helpers for a more complex opperation
        """
        self.step_description.pop()

class ProtocolSubroutine(ProtocolStep):
    """
    A special type of ProtocolStep which is used when a protocol is used as a subroutine.
    The role_assignment contains a mapping from the protocol roles to the protocol party name
    The input_variable_mapping contains, for each role, a mapping of the input variable name as mentioned
    in the subroutine to the corresponding local variable name used in the ProtocolParty
    """
    def __init__(self, subroutine_protocol: Type['AbstractProtocol'], role_assignment: dict[str, str], input_variable_mapping: dict[str, dict[str, str]]):
        super().__init__(subroutine_protocol.protocol_name)
        self.step_description: list[ProtocolStep] = subroutine_protocol.protocol_steps
        self.role_assignment = role_assignment
        self.input_variables = input_variable_mapping
