"""
This file defines all the datastructures which store the opperations being performed.
All the opperations are inherited versions of the ProtocolOpperation class.
"""

from enum import Enum
from abc import ABC
from SMPCbox.ProtocolParty import ProtocolParty
from typing import Any


class OpperationType(Enum):
    LOCAL_COMPUTATION = 0
    SEND_VARIABLES = 1
    ANNOUNCE_GLOBALS = 2

class ProtocolOpperation(ABC):
    def __init__(self, opperation_type: OpperationType, performed_by: ProtocolParty):
        self.opp_type = opperation_type
        self.party: str = performed_by.get_party_name()

class LocalComputation(ProtocolOpperation):
    def __init__(self, party: ProtocolParty, computed_variables: dict[str, Any], computation_description: str):
        super().__init__(OpperationType.LOCAL_COMPUTATION, party)
        self.computed_variables = computed_variables
        self.description = computation_description
    
    def get_description(self) -> str:
        var_string = ", ".join(self.computed_variables)
        return f"{var_string} = {self.description}"
    
    def __str__(self) -> str:
        return f"{self.party}: {self.get_description()}"

class SendVariables(ProtocolOpperation):
    def __init__(self, sender: ProtocolParty, receiver: ProtocolParty, variables: dict[str, Any]):
        super().__init__(OpperationType.SEND_VARIABLES, sender)
        self.sender = sender.get_party_name()
        self.receiver = receiver.get_party_name()
        self.send_variables = variables
    
    def __str__(self) -> str:
        return f"{self.party}: send {self.send_variables} to {self.receiver}"
    
class AnnounceGlobals(ProtocolOpperation):
    def __init__(self, announcer: ProtocolParty, variables: dict[str, Any]):
        super().__init__(OpperationType.ANNOUNCE_GLOBALS, announcer)
        self.announcer = announcer.get_party_name()
        self.announced_variables = variables
    
    def __str__(self) -> str:
        return f"{self.party}: announce {self.announced_variables}"
    

