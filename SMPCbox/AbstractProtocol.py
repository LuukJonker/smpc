from abc import ABC, abstractmethod
from typing import Union, Callable, Any
from SMPCbox.ProtocolParty import ProtocolParty

class AbstractProtocol (ABC):
    # Mandatory class variables
    parties: list[ProtocolParty]
    protocol_name: str = ""

    def __init__(self):
        self.running_party = None

        # instantiate all the ProtocolParty classes with the default name of the role.
        # These might be overwritten if the user sets them later.
        self.parties = []
        for role in self.get_party_roles():
            self.parties.append(ProtocolParty(role))
    
    """
    Returns an ordered list of the roles of each party
    For example for oblivious transfer the roles could be
    ["sender", "receiver"]
    The return of this function tels protocol users in which order to pass there
    ProtocolParty instances to the set_protocol_parties function
    """
    @abstractmethod
    def get_party_roles(self) -> list[str]:
        pass

    """
    Sets the ProtocolParty classes, the role of each party in the list should be given according
    to the order defined in the get_party_roles method.
    In the case that a user only wants to set the ProtocolParty instance for the running party
    as would be the case for most users when running distributedly then the set_running_party method should be used
    """
    def set_protocol_parties(self, parties: list[ProtocolParty]):
        if (len(parties) != len(self.get_party_roles())):
            raise Exception("The number of ProtocolParty instances provided to set_protocol_parties must be equal to the number of roles specified by get_party_roles")
        self.parties = parties

    """
    When running distributedly the party running localy should be set using this function.
    To do this a ProtocolParty instance must be provided and the role that the party should have must be specified.
    The available roles can be retrieved with the get_party_roles method.
    """
    def set_running_party(self, role: str, party: ProtocolParty):
        if not role in self.get_party_roles():
            raise Exception(f"The role \"{role}\" does not exist in the protocol\"{self.protocol_name}\"")
        self.running_party = party.get_party_name()
        idx = self.get_party_roles().index(role)
        self.parties[idx] = party

    """
    Arguments:
    party: party who should run the computation
    computed_vars: The name(s) of the new variable(s) in which to store the result from the computation. Can be str or a list of str when there are multiple results from the computation.
    input_vars: The variable(s) to use as input for the computation function. Can be a list of names or a single name string if only one argument is used.
    computation: A lambda function/function pointer which takes in the input_vars and computes the computed_vars
    description: A string describing what the computation does. This is used for protocol debugging and visualisation.
    """
    def run_computation(self, party: ProtocolParty, computed_vars: Union[str, list[str]], input_vars: Union[str, list[str]], computation: Callable, description: str):
        if (self.running_party != None and party.get_party_name() != self.running_party):
            # We don't run computations for parties that aren't the running party when a running_party is specified (when running in distributed manner).
            return
        
        party.run_computation(computed_vars, input_vars, computation, description)
    
    def add_protocol_step(self, step_name: str = None):
        for p in self.protocol_parties:
            p.add_protocol_step(step_name)

    """
    A protocol must implement the __call__ method in which the protocol is run.
    """
    @abstractmethod
    def __call__(self, running_party: str = None):
        pass

    """
    A protocol must specify what the expected inputs for each party should be.
    """
    @abstractmethod
    def get_expected_input(self) -> list[dict[str, str]]:
        pass

    """
    Gets the party with the specified role.
    """
    def get_party_with_role(self, role: str) -> ProtocolParty:
        if not role in self.get_party_roles():
            raise Exception(f"The role \"{role}\" does not exist in the protocol\"{self.protocol_name}\"")
        idx = self.get_party_roles().index(role)
        return self.parties[idx]

    """
    Sets the inputs for the protocols (all inputs specified by get_expected_input) should be given
    If set_running_party has been called only the input for that party needs to be given
    If the protocol is not run distributed then the inputs for all the parties should be provided.
    """
    def set_input(self, inputs: dict[str, dict[str, Any]]):
        for role in inputs.keys():
            party = self.get_party_with_role(role)

            for var in inputs[role].keys():
                party.set_local_variable(var, inputs[role][var])
