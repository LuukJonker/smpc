from abc import ABC, abstractmethod
from enum import Enum
from PyQt5.QtWidgets import QWidget
from typing import Any, Callable
import re
from SMPCbox.ProtocolParty import ProtocolParty
from SMPCbox.gui.ui import MainWindow


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


class StepType(Enum):
    SENDRECV = 1
    COMPUTATION = 3
    SUBROUTINE = 4
    BROADCAST = 5
    INPUT = 6
    COMMENT = 7


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
    def handle(self, all: list[ProtocolParty]) -> str:
        pass

    @abstractmethod
    def display_result(self, res: list[str]):
        pass

    @abstractmethod
    def create_widget(self, gui: MainWindow):
        pass

    def figureType(self) -> StepType:
        if isinstance(self, SendReceive):
            return StepType.SENDRECV
        elif isinstance(self, Computation):
            return StepType.COMPUTATION
        elif isinstance(self, Subroutine):
            return StepType.SUBROUTINE
        elif isinstance(self, Broadcast):
            return StepType.BROADCAST
        elif isinstance(self, Input):
            return StepType.INPUT
        elif isinstance(self, Comment):
            return StepType.COMMENT
        else:
            raise ValueError("Unknown step type")


class Comment(Step):
    def __init__(self, comment: str):
        super().__init__()
        self.comment = comment

    def __str__(self) -> str:
        return self.comment

    def handle(self, all: list[ProtocolParty]):
        return ""

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

    def create_widget(self, gui: MainWindow):
        self.widget = gui.add_comment(self.comment)


class Input(Step):
    def __init__(self, var_names: list[str], var_types: list[type]):
        super().__init__()
        self.var_names = var_names
        self.var_types = var_types

    def __str__(self) -> str:
        return str(self.var_names)

    def handle(self, all: list[ProtocolParty]):
        inputs: list[Any] = self.widget.get_inputs()
        for var_name, (i, party) in zip(self.var_names, enumerate(all)):
            party.set_local_variable(var_name, self.var_types[i](inputs[i]))

        return ""

    def display_result(self, res: list[str]):
        """Input does not display any result."""
        pass

    def create_widget(self, gui: MainWindow):
        self.widget = gui.add_input_step(self.var_names)

class SendReceive(Step):
    def __init__(self, sender: ProtocolParty, receiver: ProtocolParty, vars: list[str]):
        super().__init__()
        self.sender = sender
        self.receiver = receiver
        self.vars = vars

    def __str__(self) -> str:
        return str(self.vars)

    def handle(self, all: list[ProtocolParty]):
        self.sender.send_variables(self.receiver, self.vars)
        self.receiver.receive_variables(self.sender, self.vars)
        for var in self.vars:
            self.receiver.set_local_variable(var, self.sender.get_variable(var))

        return str([self.receiver.get_variable(v) for v in self.vars])

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

    def create_widget(self, gui: MainWindow):
        self.widget = gui.add_send_step(self.sender.name, self.receiver.name, self.vars, self.vars)


class SingleComputation:
    def __init__(
        self,
        party: ProtocolParty,
        input_vars: list[str],
        computed_vars: list[str],
        computation: Callable,
        computation_desc: str,
    ):
        super().__init__()
        self.party = party
        self.input_vars = input_vars
        self.computed_vars = computed_vars

        self.computation = computation
        self.computation_desc = computation_desc

    def __str__(self) -> str:
        return f"{self.input_vars} = {self.computation_desc}"

    def compute(self):
        res = self.party.run_computation(
            self.computed_vars, self.input_vars, self.computation, self.computation_desc
        )

        return f"{self.computed_vars} = {res}"


class Computation(Step):
    def __init__(self):
        super().__init__()

        self.all_computations: dict[str, SingleComputation] = {}

    def add_computation(
        self,
        party: ProtocolParty,
        input_vars: list[str],
        computed_vars: list[str],
        computation: Callable,
        computation_desc: str,
    ):
        self.all_computations[party.name] = SingleComputation(
            party, input_vars, computed_vars, computation, computation_desc
        )

    def __str__(self):  # type: ignore
        return str([str(comp) for comp in self.all_computations.values()])

    def handle(self, all: list[ProtocolParty]) -> list[str]:  # type: ignore
        res = []
        for party in all:
            res.append(self.all_computations[party.name].compute())

        return res

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

    def create_widget(self, gui: MainWindow):
        for comp in self.all_computations.values():
            comp_widget = gui.add_computation_step(
                comp.party.name, comp.computation_desc
            )
            self.widget = comp_widget


class Broadcast(Step):
    def __init__(self, party: ProtocolParty, vars: list[str]):
        super().__init__()
        self.party = party
        self.vars = vars

    def __str__(self) -> str:
        return f"Broadcast by {self.party.name}\n{str(self.vars)}"

    def handle(self, all: list[ProtocolParty]):
        for party in all:
            if party == self.party:
                continue

            self.party.send_variables(party, self.vars)
            party.receive_variables(self.party, self.vars)

            for var in self.vars:
                party.set_local_variable(var, self.party.get_variable(var))

        return str([self.party.get_variable(v) for v in self.vars])

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

    def create_widget(self, gui: MainWindow):
        self.widget = gui.add_broadcast(self.party.name, self.vars)


class Subroutine(Step):
    def __init__(
        self,
        protocol_class: type,
        role_assignments: dict[str, ProtocolParty],
        inputs: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        super().__init__()
        self.protocol_class = protocol_class
        self.role_assignments = role_assignments
        self.inputs = inputs
        self.output_vars = output_vars

    def __str__(self) -> str:
        return f"Subroutine {self.protocol_class.__name__}"

    def handle(self, all: list[ProtocolParty], running_local: bool = True):
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

    def create_widget(self, gui: MainWindow):
        self.widget = gui.add_subroutine_step(
            self.protocol_class.__name__,
            [party.name for party in self.role_assignments.values()],
        )


class CompiledProtocol:
    def __init__(self, parties: list[str]) -> None:
        self.parties = {party: ProtocolParty(party) for party in parties}
        self.steps: list[Step] = []
        self.input = {}
        self.output = {}

        self.indexes = {name: 0 for name in self.parties.keys()}

    def add_step(self, step: Step):
        self.steps.append(step)

    def add_comment(self, comment: str):
        self.add_step(Comment(comment))
        self.update_all_indexes()

    def add_send_receive(self, sender: str, receiver: str, vars: list[str]):
        sender_party = self.parties[sender]
        receiver_party = self.parties[receiver]
        self.add_step(SendReceive(sender_party, receiver_party, vars))

        self.update_all_indexes()

    def add_computation(
        self,
        party: str,
        computed_vars: list[str],
        input_vars: list[str],
        computation: Callable,
        computation_desc: str,
    ):
        index = self.indexes[party]

        if index >= len(self.steps):
            comp = Computation()
            comp.add_computation(
                self.parties[party],
                input_vars,
                computed_vars,
                computation,
                computation_desc,
            )
            self.add_step(comp)
        else:
            step = self.steps[index]
            if not isinstance(step, Computation):
                raise ValueError(
                    f"Expected computation step at index {index}, but got {step}"
                )

            step.add_computation(
                self.parties[party],
                input_vars,
                computed_vars,
                computation,
                computation_desc,
            )

        self.indexes[party] += 1

    def add_broadcast(self, party: str, vars: list[str]):
        self.add_step(Broadcast(self.parties[party], vars))
        self.update_all_indexes()

    def add_subroutine(
        self,
        protocol_class: type,
        role_assignments: dict[str, ProtocolParty],
        inputs: dict[str, dict[str, str]],
        output_vars: dict[str, dict[str, str]],
    ):
        self.add_step(Subroutine(protocol_class, role_assignments, inputs, output_vars))
        self.update_all_indexes()

    def update_all_indexes(self):
        highest_index = max(self.indexes.values())
        for party in self.indexes:
            self.indexes[party] = highest_index + 1
