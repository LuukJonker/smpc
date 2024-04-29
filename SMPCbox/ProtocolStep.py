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
