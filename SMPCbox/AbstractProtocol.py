from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Union, Callable, Any, TYPE_CHECKING
from SMPCbox.ProtocolParty import ProtocolParty, TrackedStatistics
from SMPCbox.ProtocolOperation import ProtocolOpperation, SendVars, Computation, Broadcast, Subroutine, Comment

if TYPE_CHECKING:
    from AbstractProtocol import AbstractProtocol

def convert_to_list(var: Union[str, list[str]]):
    list_var: list[str] = [var] if type(var) == str else list(var)
    return list_var

class AbstractProtocol(ABC):
    def __init__(self):
        # Check if the user has already specified the name of the protocol
        if not hasattr(self, "protocol_name"):
            self.protocol_name: str = "[Default Protocol Name]"

        self.parties: dict[str, ProtocolParty] = {}
        self.running_party = None
        self.protocol_output: dict[str, dict[str, Any]] = {}

        self.compiled_protocol: list[ProtocolOpperation] = []

        self.running_simulated = True

        # instantiate all the ProtocolParty classes with the default name of the role.
        # These might be overwritten if the user sets them later.
        for role in self.get_party_names():
            self.parties[role] = ProtocolParty()

    @abstractmethod
    def get_party_names(self) -> list[str]:
        """
        Returns an ordered list of the names of each party in the protocol
        For example for oblivious transfer the roles could be
        ["sender", "receiver"]
        """
        pass

    def check_name_exists(self, name: str):
        if name not in self.get_party_names():
            raise Exception(
                f'The party name "{name}" does not exist in the protocol "{self.protocol_name}"'
            )

    def set_party_addresses(self, addresses: dict[str, str], local_party_name: str | None):
        """
        This method sets the protocol to run distributedly. This method expects two arguments:

        addresses: a dictionary containing for each party name an address ("ip:port") on which 
                   that party will be listening. 
        local_party_name: the name of the party to run locally on this machine
        """

        self.running_simulated = False

        # set all the addresses
        for party_name, addr in addresses.items():
            self.check_name_exists(party_name)
            self.parties[party_name].socket.set_address(addr)

        if local_party_name is None:
            return

        # spin up the local party
        self.check_name_exists(local_party_name)
        self.running_party = local_party_name

        # ensure that the other parties are ready
        listening_socket = self.parties[local_party_name].socket
        listening_socket.start_listening()
        other_parties: list[ProtocolParty] = list(self.parties.values())
        other_parties.remove(self.parties[local_party_name])
        listening_socket.connect_to_parties(other_parties)

    def is_local_party(self, party: ProtocolParty) -> bool:
        """
        A simple helper method which checks wether the provided party should perform its computations on this machine.
        This is the case if there is no runnning party set in which case all parties are simulated on this machine.
        Or if the given party is the running party
        """
        if self.running_simulated:
            return True
        else:
            return self.running_party == self.get_name_of_party(party)

    def get_name_of_party(self, party: ProtocolParty):
        """
        Retreives the name of the given party in the current protocol
        """
        name = list(self.parties.keys())[list(self.parties.values()).index(party)]
        return name

    def compute(
        self,
        computing_party: ProtocolParty,
        computed_vars: Union[str, list[str]],
        computation: Callable,
        description: str,
    ):
        """
        Arguments:
        party: party who should run the computation
        computed_vars: The name(s) of the new variable(s) in which to store the result from the computation. Can be str or a list of str when there are multiple results from the computation.
        input_vars: The variable(s) to use as input for the computation function. Can be a list of names or a single name string if only one argument is used.
        computation: A lambda function/function pointer which takes in the input_vars and computes the computed_vars
        description: A string describing what the computation does. This is used for protocol debugging and visualisation.
        """


        computed_vars = convert_to_list(computed_vars)
        compute_opp = Computation(computing_party, computed_vars, computation, description)
        self.compiled_protocol.append(compute_opp)

    def run_computation(self, opp: Computation):
        """
        Runs a Computation, this method should Not be used by users of SMPCbox directly
        """
        if not self.is_local_party(opp.computing_party):
            # We don't run computations for parties that aren't the running party when a running_party is specified (when running in distributed manner).
            return

        opp.computing_party.run_computation(
            opp.computed_vars, opp.computation, opp.description
        )

        # Get the computed values
        computed_var_values = {}
        for name in opp.computed_vars:
            computed_var_values[name] = opp.computing_party.get_variable(name)

    def send_variables(
        self,
        sending_party: ProtocolParty,
        receiving_party: ProtocolParty,
        variables: Union[str, list[str]],
    ):
        """
        Given the party which is sending the variables and the party receiving the variables this
        method handles the sending and receiving for both of the parties.
        After a call to this method the send variables can be used in computations of the receiving_party

        Note that the variables argument can be both a single string and a list of strings in case more than one
        variable is send
        """

        variables = convert_to_list(variables)
        opp = SendVars(sending_party, receiving_party, variables)
        self.compiled_protocol.append(opp)

    def run_opperation(self, opp: ProtocolOpperation):
        """
        Runs a ProtocolOpperatino, this method should NOT be used by SMPCbox users directly.
        """

        if isinstance(opp, Computation):
            self.run_computation(opp)
        elif isinstance(opp, SendVars):
            self.run_send_variables(opp)
        elif isinstance(opp, Broadcast):
            self.run_broadcast(opp)
        elif isinstance(opp, Subroutine):
            self.run_subroutine_protocol(opp)
        else:
            pass
    
    def run_send_variables(self, opp: SendVars):
        """
        Runs a SendVars opperation, this method should not be used by SMPCbox users
        """
        # in the case that the variables is just a single string convert it to a list
        variable_values = {}

        # only call the send and receive methods on the parties if that party is running localy.
        if self.is_local_party(opp.sender):
            opp.sender.send_variables(opp.receiver, opp.vars)
            for var in opp.vars:
                variable_values[var] = opp.sender.get_variable(var)

        if self.is_local_party(opp.receiver):
            opp.receiver.receive_variables(opp.sender, opp.vars)
            if not self.is_local_party(opp.sender):
                for var in opp.vars:
                    # The variable is posibly not received yet.
                    variable_values[var] = None

    def compile_protocol(self):
        """
        After calling this method, all the opperations of the protocol will be stored in the compiled_protocol list.
        """
        self.protocol_definition()
    
    def __call__(self):
        """
        Runs the entire protocol. The party currently set as the local party will executed.
        If no local party is set the protocol will be simulated.
        """
        self.compile_protocol()

        for opp in self.compiled_protocol:
            self.run_opperation(opp)


    @abstractmethod
    def protocol_definition(self):
        """
        A protocol must implement the protocol_definition method. 
        This method should contain all the opperations of the protocol of all the parties
        """
        pass

    @abstractmethod
    def get_expected_input(self) -> dict[str, list[str]]:
        """
        A protocol must specify what the expected inputs for each party should be.
        Note that the keys of the dictionary are roles as specified by the get_party_roles method
        """
        pass

    def set_input(self, inputs: dict[str, dict[str, Any]]):
        """
        Sets the inputs for the protocols (all inputs specified by get_expected_input) should be given
        If set_running_party has been called only the input for that party needs to be given
        If the protocol is not run distributed then the inputs for all the parties should be provided.

        This method also checks wether the provided input is correct according to the get_expected_input method
        """
        expected_vars = self.get_expected_input()
        for role in inputs.keys():
            self.check_name_exists(role)

            # check wether the inputs are provided correctly for each role
            if set(expected_vars[role]) != set(inputs[role].keys()):
                expected_set = set(expected_vars[role])
                given_set = set(inputs[role].keys())
                raise Exception(
                    f"""The inputs for the role \"{role}\" in the protocol \"{self.protocol_name}\" are incorrect.\n
                                    Missing variables {expected_set.difference(given_set)}\n
                                    Provided non existent input variables {given_set.difference(expected_set)}"""
                )

            # Set the inputs
            for var in inputs[role].keys():
                self.parties[role].set_local_variable(var, inputs[role][var])

    @abstractmethod
    def output_variables(self) -> dict[str, list[str]]:
        """
        A protocol must define what output variables are produced by the protocol.
        The dictionary should contain a mapping from each role who produces output to a list of variables
        that are produced. These variables should be local variables of the ProtocolParty assigned to that role
        by the end of the protocol execution
        """
        pass

    def get_output(self) -> dict[str, dict[str, Any]]:
        """
        Using the defined output variables from the output_variables method this method returns all the values of the output variables
        """
        output = {}
        for role in self.output_variables().keys():
            self.check_name_exists(role)
            if not self.is_local_party(self.parties[role]):
                continue
            output[role] = {}
            for var in self.output_variables()[role]:
                output[role][var] = self.parties[role].get_variable(var)

        return output
    
    def add_comment(self, comment: str):
        """
        Adds a Comment opperation to the compiled protocol. This allows users to add additional explainations
        to the protocol which a GUI can visualise
        """
        self.compiled_protocol.append(Comment(comment))

    def broadcast_variables(
        self, broadcasting_party: ProtocolParty, variables: Union[str, list[str]]
    ):
        """
        Given a party who has all of the provided variables locally this method broadcasts these variables to all the parties participating in the protocol.
        After a call to this method the variables with the provided names can be used as local variables in all party.
        """

        variables = convert_to_list(variables)
        self.compiled_protocol.append(Broadcast(broadcasting_party, variables))

    def run_broadcast(self, opp: Broadcast):
        """
        Runs a Broadcast opperation, this method should NOT be used by users of SMPCbox directly
        """

        for receiver in self.parties.values():
            if receiver == opp.broadcasting_party:
                continue

            send_opp = SendVars(opp.broadcasting_party, receiver, opp.vars)
            self.run_send_variables(send_opp)

    def add_subroutine_protocol(
        self,
        protocol: AbstractProtocol,
        role_assignments: dict[str, ProtocolParty],
        inputs: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        """
        Runs the provided protocol as part of the current protocol. Apart from the protocol class (not instance), there are two required arguments:
        role_assignments: A dictionary which should map every party name within the protocol being run to an existing ProtocolParty.
                          The names can be retrieved with the get_party_roles method of the protocol class.
        inputs: Defines the variables for each role in the protocol which should be used as input. Note that this maps from roles to input variables not
                from party names to input variables.

        output_vars: Defines a mapping from the output variables of the protocol to new names.
                 For example for OT one could specify {"Receiver": {"mb": "new_name"}}.
                 This would then map the output of the OT protocol for the receiving party to the variable with the "new_name"

        Note that the keys in the inputs and role_assignments dictionaries should be roles specified in the get_party_roles method of the provided protocol
        """

        opp = Subroutine(protocol, role_assignments, inputs, output_vars)
        self.compiled_protocol.append(opp)

    def get_subroutine_input(self, opp: Subroutine) -> dict[str, dict[str, Any]]: 
        """
        A helper used internally to retrieve the input of a Subroutine protocol
        """
        input_values = {}
        # used for visualisation
        for role in opp.input_vars.keys():
            opp.protocol.check_name_exists(role)
            party = opp.role_assignments[role]

            if not self.is_local_party(party):
                # No need to set the input of non local parties
                continue

            # get the values for each of the input variables.
            input_values[role] = {}

            # we assume the user provided correct input. If not the set
            for input_var_name, provided_var in opp.input_vars[role].items():
                # Set the input variable
                if self.is_local_party(party):
                    input_values[role][input_var_name] = opp.role_assignments[
                        role
                    ].get_variable(provided_var)

            party = opp.role_assignments[role]

        return input_values


    def run_subroutine_protocol(self, opp: Subroutine):
        """
        Runs a protocol subroutine opperation, this method should NOT be used by SMPCbox users directly.
        """

        # before calling start_subroutine_protocol on the parties
        # we first gather the provided variables from the parties to avoid namespace issues.
        input_values = self.get_subroutine_input(opp)
        
        # comunicate to the participating parties that they are entering a subroutine
        for party in opp.role_assignments.values():
            party.start_subroutine_protocol(opp.protocol.protocol_name)

        # set the constructed input_values
        opp.protocol.set_input(input_values)

        # Comunicate to the protocol wether a certain party is running the protocol locally
        if self.running_party != None:
            # find what role the running_party has and set them as the running party in the subroutine protocol
            local_party_role = None
            
            for role, party in opp.role_assignments.items():
                if self.running_party == self.get_name_of_party(party):
                    local_party_role = role
            
            # Tell the protocol that it is running distributed
            opp.protocol.running_party = local_party_role
            opp.protocol.running_simulated = False
            # the addresses do not have to be provided these are in the ProtocolParty instances provided with
            # set_protocol_parties


        # run the protocol
        opp.protocol()

        # Get the output (still part of the subroutine)
        subroutine_output = opp.protocol.get_output()

        # Communicate the end of the subroutine to the parties involved
        for party in opp.role_assignments.values():
            party.end_subroutine_protocol()
    
        # now assign the output variables (not with the subroutine prefix _name_[var_name])
        self.handle_subroutine_output(opp, subroutine_output)
    
    def handle_subroutine_output(self, opp: Subroutine, subroutine_output: dict[str, dict[str, Any]]):
        """
        Retrieves the output of a run subroutine and maps the values to the new local variables
        according to the output_vars of the Subroutine.
        """

        for role in subroutine_output.keys():
            party = opp.role_assignments[role]
            if not self.is_local_party(party):
                # No need to set the output of non local parties
                continue

            for subroutine_output_var, value in subroutine_output[role].items():
                party.set_local_variable(
                    opp.output_vars[role][subroutine_output_var], value
                )

    def get_party_statistics(self) -> dict[str, TrackedStatistics]:
        """
        Returns the statistics of each party in the protocol
        The return is a dictionary with each role mapping to the statistics of that party
        """
        stats = {}
        for role, party in self.parties.items():
            stats[role] = party.get_statistics()

        return stats
    
    def set_protocol_parties(self, role_assignments: dict[str, ProtocolParty]):
        """
        This method should NOT be used by users of SMPCbox. Method is used internally
        """

        if set(role_assignments.keys()) != set(self.get_party_names()):
            raise Exception(
                "A ProtocolParty instance should be provided for every role in the protocol when calling set_protocol_parties."
            )
        self.parties = role_assignments
    
    def get_total_statistics(self) -> TrackedStatistics:
        """
        This method returns the agregated statistics of all the parties.
        This is the same data as returned from the get_party_statistics method
        """
        total_stats = TrackedStatistics()
        for party in self.parties.values():
            party_stats: TrackedStatistics = party.get_statistics()
            total_stats += party_stats
        
        return total_stats

    def terminate_protocol(self):
        """
        This method cleans up the ProtocolParty instances by calling exit_protocol on each ProtocolParty.

        WARNING! do not use this method in the implementation of a protocol. This method should only be called from outside the protocol
        since a protocol might be used as a subroutine in a larger protocol in which case the ProtocolParty instances could still be in use
        even if the protocol ends.
        """
        for p in self.parties.values():
            p.exit_protocol()
