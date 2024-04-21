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

class ProtocolSubroutine(ProtocolStep):
    """
    A special type of ProtocolStep which is used when a protocol is used as a subroutine
    """
    def __init__(self, subroutine_protocol: Type['AbstractProtocol']):
        super().__init__(subroutine_protocol.protocol_name)
        self.step_description: list[ProtocolStep] = subroutine_protocol.protocol_steps
