from abc import ABC, abstractmethod
from enum import Enum
from PyQt5.QtWidgets import QWidget
from typing import Any, Callable
import re
from SMPCbox.ProtocolParty import ProtocolParty


def replace_variables(expression: str, variables: dict[str, Any]):
    # Regular expression to match variable names
    variable_pattern = re.compile(r"\b[a-zA-Z_]\w*\b")

    # Function to replace a match with its corresponding value from the dictionary
    def variable_replacer(match):
        var_name = match.group(0)
        return str(variables.get(var_name, var_name))

    # Replace all variables in the expression using the replacer function
    result = variable_pattern.sub(variable_replacer, expression)

    return result


class Client:
    def __init__(self, name: str):
        self.party = ProtocolParty(name)
        self.steps: list["Step"] = []
        self.vars: dict[str, Any] = {}

    def add_step(self, step: "Step"):
        self.steps.append(step)

    @property
    def name(self):
        return self.party.name


class StepType(Enum):
    SEND = 1
    RECV = 2
    COMPUTATION = 3
    SUBROUTINE = 4
    BROADCAST = 5
    INPUT = 6


class Step(ABC):
    def __init__(self):
        self.type: StepType = self.figureType()
        self.widget: QWidget

    def __repr__(self) -> str:
        return str(self)

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def handle(self, yourself: Client, all: list[Client]) -> str:
        pass

    @abstractmethod
    def display_result(self, res: list):
        pass

    def figureType(self) -> StepType:
        if isinstance(self, Send):
            return StepType.SEND
        elif isinstance(self, Computation):
            return StepType.COMPUTATION
        elif isinstance(self, Subroutine):
            return StepType.SUBROUTINE
        elif isinstance(self, Broadcast):
            return StepType.BROADCAST
        elif isinstance(self, Input):
            return StepType.INPUT
        else:
            raise ValueError("Unknown step type")


class Comment(Step):
    def __init__(self, comment: str):
        super().__init__()
        self.comment = comment

    def __str__(self) -> str:
        return self.comment

    def handle(self, yourself: Client, all: list[Client]):
        return ""

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Send(Step):
    def __init__(self, receiver: Client, vars: list[str]):
        super().__init__()
        self.receiver = receiver
        self.vars = vars

    def __str__(self) -> str:
        return str(self.vars)

    def handle(self, yourself: Client, all: list[Client]):
        yourself.party.send_variables(self.receiver.party, self.vars)
        for var in self.vars:
            self.receiver.vars[var] = yourself.vars[var]

        return str([self.receiver.vars[v] for v in self.vars])

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Receive(Step):
    def __init__(self, sender: Client, vars: list[str]):
        super().__init__()
        self.sender = sender
        self.vars = vars

    def __str__(self) -> str:
        return str(self.vars)

    def handle(self, yourself: Client, all: list[Client]):
        yourself.party.receive_variables(self.sender.party, self.vars)
        return str([self.sender.vars[v] for v in self.vars])

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Computation(Step):
    def __init__(self, input_vars: list[str], computed_vars: list[str], computation: Callable, computation_desc: str):
        super().__init__()
        self.input_vars = input_vars
        self.computed_vars = computed_vars

        self.computation = computation
        self.computation_desc = computation_desc

    def __str__(self) -> str:
        return f"{self.input_vars} = {self.computation_desc}"

    def handle(self, yourself: Client, all: list[Client]):
        res = yourself.party.run_computation(
            self.computed_vars, self.input_vars, self.computation, self.computation_desc
        )

        return f"{self.computed_vars} = {res}"

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Broadcast(Step):
    def __init__(self, party: Client, vars: list[str]):
        super().__init__()
        self.party = party
        self.vars = vars

    def __str__(self) -> str:
        return f"Broadcast by {self.party.name}\n{str(self.vars)}"

    def handle(self, yourself: Client, all: list[Client]):
        for client in all:
            if client == yourself:
                continue

            yourself.party.send_variables(client.party, self.vars)
            client.party.receive_variables(yourself.party, self.vars)

            for var in self.vars:
                client.vars[var] = yourself.vars[var]

        return str([yourself.vars[v] for v in self.vars])

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Subroutine(Step):
    from SMPCbox.AbstractProtocol import AbstractProtocol

    def __init__(
        self,
        protocol_class: type[AbstractProtocol],
        role_assignments: dict[str, ProtocolParty],
        inputs: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        super().__init__()
        self.protocol_class = protocol_class
        self.role_assignments = role_assignments
        self.inputs = inputs
        self.output_vars = output_vars

        self.leader = True

    def __str__(self) -> str:
        return f"Subroutine {self.protocol_class.__name__}"

    def handle(self, yourself: Client, all: list[Client], running_local: bool = True):
        if not self.leader:
            return ""

        protocol = self.protocol_class()
        protocol.set_protocol_parties(self.role_assignments)

        # before calling start_subroutine_protocol on the parties
        # we first gather the provided variables from the parties to avoid namespace issues.
        input_values = {}
        # used for visualisation
        input_var_mapping = {}
        for role in self.inputs.keys():
            protocol.check_role_exists(role)
            party = self.role_assignments[role]

            if not running_local:
                # No need to set the input of non local parties
                continue

            # get the values for each of the input variables.
            input_values[role] = {}
            input_var_mapping[role] = {}

            # we assume the user provided correct input. If not the set
            for input_var_name, provided_var in self.inputs[role].items():
                # Set the input variable
                if running_local:
                    input_values[role][input_var_name] = self.role_assignments[
                        role
                    ].get_variable(provided_var)
                    input_var_mapping[role][input_var_name] = provided_var

            party = self.role_assignments[role]

        # comunicate to the participating parties that they are entering a subroutine
        for party in self.role_assignments.values():
            party.start_subroutine_protocol(protocol.protocol_name)

        # set the constructed input_values
        protocol.set_input(input_values)

        # # Comunicate to the protocol wether a certain party is running the protocol locally
        # if self.running_party != None:
        #     # find what role the running_party has and set them as the running party in the subroutine protocol
        #     for role, party in role_assignments.items():
        #         if self.running_party == party.name:
        #             protocol.set_running_party(role, party)

        # run the protocol
        protocol()

        # Get the output and
        subroutine_output = protocol.get_output()

        for role in subroutine_output.keys():
            party = self.role_assignments[role]
            if not running_local:
                # No need to set the output of non local parties
                continue

            for subroutine_output_var, value in subroutine_output[role].items():
                party.set_local_variable(
                    self.output_vars[role][subroutine_output_var], value
                )

        return ""

    def display_result(self, res: list[str]):
        """Subroutine does not display any result."""
        pass


class Input(Step):
    def __init__(self, var_names: list[str], var_type: type):
        super().__init__()
        self.var_names = var_names
        self.var_type = var_type

    def __str__(self) -> str:
        return str(self.var_names)

    def handle(self, yourself: Client, all: list[Client]):
        inputs: list[Any] = self.widget.get_inputs()
        for var_name, (i, client) in zip(self.var_names, enumerate(all)):
            client.vars[var_name] = self.var_type(inputs[i])

        return ""

    def display_result(self, res: list[str]):
        """Input does not display any result."""
        pass


class CompiledProtocol:
    from SMPCbox.AbstractProtocol import AbstractProtocol

    def __init__(self, parties: list[str]) -> None:
        self.clients = {party: Client(party) for party in parties}
        self.input = {}
        self.output = {}

    def add_comment(self, comment: str):
        for client in self.clients.values():
            client.add_step(Comment(comment))

    def add_send_receive(self, sender: str, receiver: str, vars: list[str]):
        sender_client = self.clients[sender]
        receiver_client = self.clients[receiver]
        sender_client.add_step(Send(receiver_client, vars))
        receiver_client.add_step(Receive(sender_client, vars))

    def add_computation(
        self,
        party: str,
        computed_vars: list[str],
        input_vars: list[str],
        computation: Callable,
        computation_desc: str,
    ):
        self.clients[party].add_step(Computation(input_vars, computed_vars, computation, computation_desc))

    def add_broadcast(self, party: str, vars: list[str]):
        self.clients[party].add_step(Broadcast(self.clients[party], vars))

    def add_subroutine(
        self,
        protocol_class: type[AbstractProtocol],
        role_assignments: dict[str, ProtocolParty],
        inputs: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        for i, client in enumerate(role_assignments.values()):
            step = Subroutine(protocol_class, role_assignments, inputs, output_vars)

            # Only the first party is the leader
            if i == 0:
                step.leader = True
            else:
                step.leader = False

            self.clients[client.name].add_step(step)


    def finalize(self):
        done = [False] * len(self.clients)
        indexes = {name: 0 for name in self.clients.keys()}

        while not all(done):
            current_steps = []
            should_increment = [False] * len(self.clients)

            for i, client in enumerate(self.clients.values()):
                if done[i]:
                    current_steps.append(None)
                    continue

                step = client.steps[indexes[client.name]]

                if isinstance(step, Subroutine):
                    participants = [party.name for party in step.role_assignments.values()]
                    if not all([isinstance(self.clients[party].steps[indexes[party]], Subroutine) for party in participants]):
                        continue

                elif isinstance(step, Send):





                current_steps.append(step)

                should_increment[i] = True

                if indexes[client.name] == len(client.steps):
                    done[i] = True

            for i, client in enumerate(self.clients.values()):
                if should_increment[i]:
                    indexes[client.name] += 1

