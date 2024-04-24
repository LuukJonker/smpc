from abc import ABC, abstractmethod
from typing import Union, Callable, Any, Type
from SMPCbox.ProtocolParty import ProtocolParty
from SMPCbox.ProtocolStep import ProtocolStep, ProtocolSubroutine
from SMPCbox.ProtocolOpps import LocalComputation, SendVariables, AnnounceGlobals

class AbstractProtocol (ABC):
    # Mandatory class variables
    
    # The name of the protocol
    protocol_name: str = ""
    
    # A mapping from each role in the protocol to a ProtocolParty instance
    parties: dict[str, ProtocolParty] = {}
    
    # A list storing all the protocol steps. The ProtocolStep class is used to store the description of what happens in each step
    protocol_steps: list[Union[ProtocolStep, ProtocolSubroutine]] = []

    # protocol_output
    protocol_output: dict[str, dict[str, Any]] = None


    def __init__(self):
        self.running_party = None

        # instantiate all the ProtocolParty classes with the default name of the role.
        # These might be overwritten if the user sets them later.
        for role in self.get_party_roles():
            self.parties[role] = ProtocolParty(role)

    @abstractmethod
    def get_party_roles(self) -> list[str]:
        """
        Returns an ordered list of the roles of each party
        For example for oblivious transfer the roles could be
        ["sender", "receiver"]
        The return of this function tels protocol users in which order to pass there
        ProtocolParty instances to the set_protocol_parties function
        """
        pass

    def set_protocol_parties(self, role_assignments: dict[str, ProtocolParty]):
        """
        Sets the ProtocolParty classes, the dictionary should contain a mapping from every role specified by get_party_roles to a
        ProtocolParty instance.
        
        The use of this method is not mandatory, if the parties are never set then the protocol class automaticaly creates ProtocolParty
        instances with the names of the roles in the protocol.
    
        Note that in the case that the protocol is run distributedly the party running localy should also be specified with the
        set_running_party method.

        WARNING: Any data, such as input set with the set_input method, which is already stored in the existing ProtocolParty classes
        is lost once this method is called.
        """

        party_names = set(party.name for party in role_assignments.values())
        if len(party_names) != len(role_assignments.values()):
            raise Exception("Make sure each ProtocolParty partaking in a protocol has a unique name!")

        if set(role_assignments.keys()) != set(self.get_party_roles()):
            raise Exception("A ProtocolParty instance should be provided for every role in the protocol when calling set_protocol_parties.")
        self.parties = role_assignments
    
    def check_role_exists(self, role: str):
        if not role in self.get_party_roles():
            raise Exception(f"The role \"{role}\" does not exist in the protocol\"{self.protocol_name}\"")

    def set_running_party(self, role: str, party: ProtocolParty):
        """
        When running distributedly the party running localy should be set using this function.
        To do this a ProtocolParty instance must be provided and the role that the party should have must be specified.
        The available roles can be retrieved with the get_party_roles method.
        """
        self.check_role_exists(role)
        self.running_party = party.name

    def is_local_party(self, party: ProtocolParty) -> bool:
        """
        A simple helper method which checks wether the provided party should perform its computations on this machine.
        This is the case if there is no runnning party set in which case all parties are simulated on this machine.
        Or if the given party is the running party
        """
        return self.running_party == None or self.running_party == party.name
    
    def in_protocol_step(self):
        """
        A helper method that checks wether the last item in self.protocol_steps is an instance
        of the ProtocolStep class and not a ProtocolSubroutine.
        This is used to ensure that any ProtocolOpperations being added have a ProtocolStep in which they can be added
        """
        if len(self.protocol_steps) == 0:
            raise Exception("No protocol step defined to add a protocol opperation to.\nTo add a protocol step call the add_protocol_step method!")
        
        if  isinstance(self.protocol_steps, ProtocolSubroutine):
            raise Exception("No protocol step defined to add a protocol opperation to.\nAfter calling run_subroutine_protocol please add a new step with the add_protocol_step method!")
        

    def compute(self, computing_party: ProtocolParty, computed_vars: Union[str, list[str]], input_vars: Union[str, list[str]], computation: Callable, description: str):
        """
        Arguments:
        party: party who should run the computation
        computed_vars: The name(s) of the new variable(s) in which to store the result from the computation. Can be str or a list of str when there are multiple results from the computation.
        input_vars: The variable(s) to use as input for the computation function. Can be a list of names or a single name string if only one argument is used.
        computation: A lambda function/function pointer which takes in the input_vars and computes the computed_vars
        description: A string describing what the computation does. This is used for protocol debugging and visualisation.
        """

        # Verify the existence of a current protocol step
        self.in_protocol_step()

        if (not self.is_local_party(computing_party)):
            # We don't run computations for parties that aren't the running party when a running_party is specified (when running in distributed manner).
            return


        computing_party.run_computation(computed_vars, input_vars, computation, description)
        
        # Make sure to prefix the namespace to the computed vars in the visualisation
        computed_vars = [computed_vars] if type(computed_vars) == str else computed_vars
        computed_var_names = [computing_party.get_namespace() + var for var in computed_vars]

        # Get the computed values
        computed_var_values = {}
        for name in computed_var_names:
            computed_var_values[name] = computing_party.get_variable(name)

        # add the local computation
        self.protocol_steps[-1].add_opperation(LocalComputation(computing_party, computed_var_names, description))
    
    def add_protocol_step(self, step_name: str = None):
        """
        Declares the start of a new round/step of the protocol.
        Any calls to run_computation after a call to this method will be ran as part of this step.
        """
        if step_name == None:
            step_name = f"step_{len(self.protocol_steps + 1)}"

        self.protocol_steps.append(ProtocolStep(step_name))
    
    def send_variables(self, sending_party: ProtocolParty, receiving_party: ProtocolParty, variables: Union[str, list[str]]):
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
        variables = [variables] if type(variables) == str else variables
        variable_values = {}

        # TODO change the send and receive methods for protocol parties to send multiple variables as one message.
        for var in variables:
            # only call the send and receive methods on the parties if that party is running localy.
            if (self.is_local_party(sending_party)):
                sending_party.send_variable(receiving_party, var)
                variable_values[var] = sending_party.get_variable(var)
            
            if (self.is_local_party(receiving_party)):
                receiving_party.receive_variable(sending_party, var)
                if var not in variable_values.keys():
                    # TODO set to none when the get_variable becomes blocking.
                    # TODO add a ReceivedVar to the protocolOpps
                    variable_values[var] = receiving_party.get_variable(var)
        
        # add the description
        self.protocol_steps[-1].add_opperation(SendVariables(sending_party, receiving_party, variable_values))
        

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

        WARNING: This method uses the ProtocolParty classes to store the provided input. Calling set_protocol_parties 
        after a call to this method thus erases the input.
        """
        expected_vars = self.get_expected_input()
        for role in inputs.keys():
            self.check_role_exists(role)

            # check wether the inputs are provided correctly for each role
            if set(expected_vars[role]) != set(inputs[role].keys()):
                expected_set = set(expected_vars[role])
                given_set = set(inputs[role].keys())
                raise Exception(f"""The inputs for the role \"{role}\" in the protocol \"{self.protocol_name}\" are incorrect.\n
                                    Missing variables {expected_set.difference(given_set)}\n
                                    Provided non existent input variables {given_set.difference(expected_set)}""")
            
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
            self.check_role_exists(role)
            if not self.is_local_party(self.parties[role]):
                continue
            output[role] = {}
            for var in self.output_variables()[role]:
               output[role][var] = self.parties[role].get_variable(var)

        return output


    def announce_globals(self, announcing_party: ProtocolParty, variables: Union[str, list[str]]):
        """
        Given a party who has all of the provided variables localy this method announces the globals to all the parties participating in the protocol.
        After a call to this method the variables with the provided names can be used as local variables in all party.
        """

        variables = variables if type(variables) == list else [variables]
        
        # Verify the existence of a current protocol step
        self.in_protocol_step()

        for receiver in self.parties.values():
            if receiver == announcing_party:
                continue
            self.send_variables(announcing_party, receiver, variables)
            # Remove the SendVariables since it will be replaced by an AnnounceGlobals
            self.protocol_steps[-1].remove_last_opperation()

        self.protocol_steps[-1].add_opperation(AnnounceGlobals(announcing_party, variables))

    
    def run_subroutine_protocol(self, protocol: Type['AbstractProtocol'], role_assignments: dict[str, ProtocolParty], inputs: dict[str, list[str]]):
        """
        Runs the provided protocol as part of the current protocol. Appart from the protocol class (not instance), there are two required arguments:
        role_assignments: A dictionary which should map every role of the protocol being run to an existing ProtocolParty.
                          The roles can be retreived with the get_party_roles method of the protocol class.
        inputs: Defines the variables for each role in the protocol which should be used as input. Note that this maps from roles to input variables not
                from party names to input variables.
            
        Note that the keys in the inputs and role_assignments dictionaries should be roles specified in the get_party_roles method of the provided protocol
        """

        p = protocol()

        # before calling start_subroutine_protocol on the parties
        # we first gather the provided variables from the parties to avoid namespace issues.
        input_values = {}
        # used for visualisation
        input_var_mapping = {}
        for role in inputs.keys():
            self.check_role_exists(role)
            party = role_assignments[role]

            if not self.is_local_party(party):
                # No need to set the input of non local parties
                continue

            # get the values for each of the input variables.
            input_values[role] = {}
            input_var_mapping[role] = {}
            expected_input_vars = p.get_expected_input()[role]
            for input_var_name, provided_var in zip(expected_input_vars, inputs[role]):
                # Set the input variable
                if (self.is_local_party(party)):
                    input_values[input_var_name] = role_assignments[role].get_variable(provided_var)
                    input_var_mapping[input_var_name] = provided_var

            party = role_assignments[role]

        # comunicate to the participating parties that they are entering a subroutine
        for party in role_assignments.values():
            party.start_subroutine_protocol(protocol.protocol_name)

        p.set_protocol_parties(role_assignments)

        # Comunicate to the protocol wether a certain party is running the protocol localy
        if self.running_party != None:
            # find what role the running_party has and set them as the running party in the subroutine protocol
            for role, party in role_assignments.items():
                if self.running_party == party.name:
                    protocol.set_running_party(role, party)
        
        
        # set the constructed input_values
        p.set_input(input_values)

        # run the protocol
        p()

        # Comunicate the end of the subroutine to the parties involved
        for party in role_assignments.values():
            party.end_subroutine_protocol()
        
        self.protocol_steps.append(ProtocolSubroutine(protocol, role_assignments, input_var_mapping))

    
    def terminate_protocol(self):
        """
        This method cleans up the ProtocolParty instances by calling exit_protocol on each ProtocolParty.
        
        WARNING! do not use this method in the implementation of a protocol. This method should only be called from outside the protocol
        since a protocol might be used as a subroutine in a larger protocol in which case the ProtocolParty instances could still be in use
        even if the protocol ends.
        """
        for p in self.parties.values():
            p.exit_protocol()
