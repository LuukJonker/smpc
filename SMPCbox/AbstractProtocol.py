from abc import ABC, abstractmethod
from typing import Union, Callable, Any, Type
from SMPCbox.ProtocolParty import ProtocolParty, TrackedStatistics
from SMPCbox.ProtocolStep import ProtocolStep

def convert_to_list(var: Union[str, list[str]]):
    list_var: list[str] = [var] if type(var) == str else list(var)
    return list_var


class AbstractProtocolVisualiser(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def add_computation(
        self,
        computing_party_name: str,
        computed_vars: dict[str, Any],
        computation: str
    ):
        """
        This method visualises a computation.
        Args:
            computing_party_name (str): The name of the party performing the computation.
            computed_vars (dict[str, Any]): A dictionary of all the (new) variables which have been computed and their values.
            computation (str): A string description of the computation.
        """
        pass

    @abstractmethod
    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        """
        This method should implement the visualisation of message sending.
        Args:
            sending_party_name (str): The name of the party sending the variable(s).
            receiving_party_name (str): The name of the party receiving the variable(s).
            variables (dict[str, Any]): A dictionary containing the names and values of all variable(s) being send.
        """
        pass

    @abstractmethod
    def broadcast_variables(
        self, broadcasting_party_name: str, variables: dict[str, Any]
    ):
        """
        This method should implement the visualisation of a broadcast.
        Args:
            broadcasting_party_name (str): The name of the party broadcasting the variable(s).
            variables (dict[str, Any]): A dictionary containing the names and values of all variable(s) being send.
        """
        pass

    @abstractmethod
    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        """
        Visualise the start a new subroutine, all subsequent calls to methods of the ProtocolVisualiser are from within the subroutine

        Args:
            subroutine_name (str): The name of the protocol which is run as a subroutine.
            party_mapping (dict[str, str]): A dictionary which contains the names of parties in the current protocol and maps them to names within the new protocol which is run as a subroutine.
            input_mapping (dict[str, dict[str, str]]): For each party in the current protocol (which participates in the subroutine) a dictionary is provided which maps an existing variable to some input variable of the subroutine protocol
            output_mapping (dict[str, dict[str, str]]): For each party in the current protocol (which participates in the subroutine) a dictionary is provided which maps the output variables to a variable with some specified name outside of the subroutine.
        """
        pass

    @abstractmethod
    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        """
        This method tells the ProtocolVisualiser that the subroutine we are in has ended. We thus return to the protocol which called the subroutine protocol originaly.
        Any subsequent calls to the ProtocolVisualiser are thus from the protocol which was running before a subroutine was run.

        Args:
            output_values (dict[str, dict[str, Any]]): For each party (names from within the subroutine), the dictionary contains all the output variables and their values.
        """
        pass


class EmptyVisualiser(AbstractProtocolVisualiser):
    """
    This class is used when no visualiser is provided and does nothing when the visualisation methods are called.
    """

    def __init__(self):
        pass

    def add_computation(
        self,
        computing_party_name: str,
        computed_vars: dict[str, Any],
        computation: str
    ):
        pass

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        pass

    def broadcast_variables(
        self, broadcasting_party_name: str, variables: dict[str, Any]
    ):
        pass

    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        pass

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        pass


class AbstractProtocol(ABC):
    def __init__(self):
        # Check if the user has already specified the name of the protocol
        if not hasattr(self, "protocol_name"):
            self.protocol_name: str = "[Default Protocol Name]"

        self.parties: dict[str, ProtocolParty] = {}
        self.running_party = None
        self.protocol_steps: list[ProtocolStep] = []
        self.protocol_output: dict[str, dict[str, Any]] = {}
        self.visualiser: AbstractProtocolVisualiser = EmptyVisualiser()

        self.running_simulated = True

        # A flag used to disable the visualisation for message sending if the message sending is part of a broadcast opperation
        self.broadcasting = False

        # instantiate all the ProtocolParty classes with the default name of the role.
        # These might be overwritten if the user sets them later.
        for role in self.get_party_names():
            self.parties[role] = ProtocolParty()

    def set_protocol_visualiser(self, visualiser: AbstractProtocolVisualiser):
        """
        This method is used by a gui to provide their own implementation of the AbstractProtocolVisualiser.
        The methods of their own implementation are then called appropriately with information regarding the protocol execution.
        """
        self.visualiser = visualiser

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

    def in_protocol_step(self):
        """
        A helper method that checks wether the last item in self.protocol_steps is an instance
        of the ProtocolStep class and not a ProtocolSubroutine.
        This is used to ensure that any ProtocolOpperations being added have a ProtocolStep in which they can be added
        """
        if len(self.protocol_steps) == 0:
            raise Exception(
                "No protocol step defined to add a protocol opperation to.\nTo add a protocol step call the add_protocol_step method!"
            )

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

        # Verify the existence of a current protocol step
        self.in_protocol_step()

        if not self.is_local_party(computing_party):
            # We don't run computations for parties that aren't the running party when a running_party is specified (when running in distributed manner).
            return

        computing_party.run_computation(
            computed_vars, computation, description
        )

        # Get the computed values
        computed_var_values = {}
        for name in computed_vars:
            computed_var_values[name] = computing_party.get_variable(name)

        # add the local computation
        self.visualiser.add_computation(
            self.get_name_of_party(computing_party),
            computed_var_values,
            description
        )

    def add_protocol_step(self, step_name: str = ""):
        """
        Declares the start of a new round/step of the protocol.
        Any calls to run_computation after a call to this method will be ran as part of this step.
        """
        if step_name == "":
            step_name = f"step_{len(self.protocol_steps) + 1}"

        self.protocol_steps.append(ProtocolStep(step_name))

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
        # Verify the existence of a current protocol step
        self.in_protocol_step()

        # in the case that the variables is just a single string convert it to a list
        variables = convert_to_list(variables)
        variable_values = {}

        # only call the send and receive methods on the parties if that party is running localy.
        if self.is_local_party(sending_party):
            sending_party.send_variables(receiving_party, variables)
            for var in variables:
                variable_values[var] = sending_party.get_variable(var)

        if self.is_local_party(receiving_party):
            receiving_party.receive_variables(sending_party, variables)
            if not self.is_local_party(sending_party):
                for var in variables:
                    # The variable is posibly not received yet.
                    variable_values[var] = None

        if not self.broadcasting:
            sending_party_name = self.get_name_of_party(sending_party)
            receiving_party_name = self.get_name_of_party(receiving_party)
            self.visualiser.send_message(
                sending_party_name, receiving_party_name, variable_values
            )

    @abstractmethod
    def __call__(self):
        """
        A protocol must implement the __call__ method in which the protocol is run.
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

    def broadcast_variables(
        self, broadcasting_party: ProtocolParty, variables: Union[str, list[str]]
    ):
        """
        Given a party who has all of the provided variables locally this method broadcasts these variables to all the parties participating in the protocol.
        After a call to this method the variables with the provided names can be used as local variables in all party.
        """

        self.broadcasting = True

        variables = convert_to_list(variables)

        # Verify the existence of a current protocol step
        self.in_protocol_step()

        for receiver in self.parties.values():
            if receiver == broadcasting_party:
                continue

            self.send_variables(broadcasting_party, receiver, variables)

        var_values = {var: broadcasting_party.get_variable(var) for var in variables}

        self.visualiser.broadcast_variables(
            self.get_name_of_party(broadcasting_party), var_values
        )

        self.broadcasting = False

    def run_subroutine_protocol(
        self,
        protocol_class: Type["AbstractProtocol"],
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

        protocol = protocol_class()
        protocol.set_protocol_parties(role_assignments)

        role_assignments_names = {
            role: self.get_name_of_party(party)
            for role, party in role_assignments.items()
        }

        # before calling start_subroutine_protocol on the parties
        # we first gather the provided variables from the parties to avoid namespace issues.
        input_values = {}
        # used for visualisation
        input_var_mapping = {}
        for role in inputs.keys():
            protocol.check_name_exists(role)
            party = role_assignments[role]

            if not self.is_local_party(party):
                # No need to set the input of non local parties
                continue

            # get the values for each of the input variables.
            input_values[role] = {}
            input_var_mapping[role] = {}

            # we assume the user provided correct input. If not the set
            for input_var_name, provided_var in inputs[role].items():
                # Set the input variable
                if self.is_local_party(party):
                    input_values[role][input_var_name] = role_assignments[
                        role
                    ].get_variable(provided_var)
                    input_var_mapping[role][input_var_name] = provided_var

            party = role_assignments[role]

        # comunicate to the participating parties that they are entering a subroutine
        for party in role_assignments.values():
            party.start_subroutine_protocol(protocol.protocol_name)

        # set the constructed input_values
        protocol.set_input(input_values)

        # Comunicate to the protocol wether a certain party is running the protocol locally
        if self.running_party != None:
            # find what role the running_party has and set them as the running party in the subroutine protocol
            local_party_role = None
            
            for role, party in role_assignments.items():
                if self.running_party == self.get_name_of_party(party):
                    local_party_role = role
            
            # Tell the protocol that it is running distributed
            protocol.running_party = local_party_role
            protocol.running_simulated = False
            # the addresses do not have to be provided these are in the ProtocolParty instances provided with
            # set_protocol_parties


        # tell the visualiser we will be running a subroutine.
        self.visualiser.start_subroutine(
            protocol.protocol_name, role_assignments_names, input_values, output_vars
        )

        # run the protocol
        protocol()

        # Get the output (still part of the subroutine)
        subroutine_output = protocol.get_output()

        # Communicate the end of the subroutine to the parties involved
        for party in role_assignments.values():
            party.end_subroutine_protocol()

        # now assign the output variables (not with the subroutine prefix _name_[var_name])
        for role in subroutine_output.keys():
            party = role_assignments[role]
            if not self.is_local_party(party):
                # No need to set the output of non local parties
                continue

            for subroutine_output_var, value in subroutine_output[role].items():
                party.set_local_variable(
                    output_vars[role][subroutine_output_var], value
                )

        self.visualiser.end_subroutine(subroutine_output)

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

    def get_protocol_steps(self) -> list[ProtocolStep]:
        """
        Retrieves all of the protocol steps containing the opperations performed by the protocol.
        If the protocol has not yet been called this returns an empty list.
        """
        return self.protocol_steps

    def terminate_protocol(self):
        """
        This method cleans up the ProtocolParty instances by calling exit_protocol on each ProtocolParty.

        WARNING! do not use this method in the implementation of a protocol. This method should only be called from outside the protocol
        since a protocol might be used as a subroutine in a larger protocol in which case the ProtocolParty instances could still be in use
        even if the protocol ends.
        """
        for p in self.parties.values():
            p.exit_protocol()
