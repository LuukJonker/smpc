from __future__ import annotations
from abc import ABC
from typing import Callable, TYPE_CHECKING
from SMPCbox.ProtocolParty import ProtocolParty

if TYPE_CHECKING:
    from AbstractProtocol import AbstractProtocol

class ProtocolOpperation(ABC):
    pass

class SendVars(ProtocolOpperation):
    """
    Stores any information needed for the Sending of variables.
    The stored attributes are:

    receiver: ProtocolParty
        This attribute stores the ProtocolParty who will receive the variables
    sender: ProtocolParty
        This attribute stores the ProtocolParty who will send the variables
    vars: list[str]
        A list of variable names. These variables are local variables to the sender ProtocolParty.
    """
    def __init__(self, sender: ProtocolParty, receiver: ProtocolParty, vars: list[str]):
        self.receiver = receiver
        self.sender = sender
        self.vars = vars


class Computation(ProtocolOpperation):
    """
    Stores any information needed for a local Computation.
    The stored attributes are:
    
    computing_party: ProtocolParty
        This stores the ProtocolParty who will perform this computation locally.
    computed_vars: list[str]
        Contains the variable(s) which are produced by the computation.
        These variables are then set as local variables when performing the computation.
    computation: Callable
        Stores the function object which, when called performs the computation
    description: str
        Describes what the computation does, this can be used for visualisation.
    """
    def __init__(self, computing_party: ProtocolParty, computed_vars: list[str], computation: Callable, description: str):
        self.computing_party = computing_party
        self.computed_vars = computed_vars

        self.computation = computation
        self.description = description

class Broadcast(ProtocolOpperation):
    """
    Stores any information needed for a Broadcast.
    The stored attributes are:
    
    broadcasting_party: ProtocolParty
        The ProtcolParty broadcasting their local variables.
    vars: list[str]
        The variable(s) being broadcasted. After running the broadcast these variables will be known 
        to all the parties in the protocol
    """
    def __init__(self, broadcasting_party: ProtocolParty, vars: list[str]):
        self.broadcasting_party = broadcasting_party
        self.vars = vars

class Subroutine(ProtocolOpperation):
    """
    Stores Any information needed to run a protocol as a subroutine.
    The stored attributes are:

    protocol:  AbstractProtocol
        An instance of the protocol which should be run.
    role_assignments: dict[str, ProtocolParty]
        The ProtocolParty instances which should act as parties with a specific name in the subroutine.
        For example in the Oblivious Transfer protocol one could pass:
        {"Sender": self.parties["Alice"], "Receiver": self.parties["Bob"]}
        to set Alice as the Sender and Bob as the Receiver.
    input_vars: dict[str, dict[str, str]]
        The local variables of each party to be used as inputs for the subroutine.
        An example input when running Oblivious Transfer could be:
        {"Sender": {"m0": "m0_input", "m1": "m1_input"}, "Receiver": {"b": "b_i"}}

        In this case this would signal that the party who will run as the "Sender" has the local variables 
        "m0_input" and "m1_input" which should be used as "m0" and "m1" in the Oblibious Transfer protocol whilst
        the party who will run as the "Receiver" has a local variable "b_i" which should be used as "b" in the protocol.
    output_vars: dict[str, dict[str,str]]
        Similarly to the input_vars this provides a mapping to perform from the output of the subroutine to specific local variables.
        An example for this value could be:
        {"Receiver": {"mb": "my_var"}}
        Which will result in the output variable "mb" of the subroutine being stored in the local variable "my_var" after the
        subroutine.
    """
    def __init__(
        self,
        protocol: AbstractProtocol,
        role_assignments: dict[str, ProtocolParty],
        input_vars: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        self.protocol = protocol
        self.protocol.set_protocol_parties(role_assignments)
        self.protocol.compile_protocol()
        self.role_assignments = role_assignments
        self.input_vars = input_vars
        self.output_vars = output_vars
    
class Comment(ProtocolOpperation):
    def __init__(self, comment: str):
        self.comment = comment