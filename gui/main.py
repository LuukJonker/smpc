from typing import Any
from abc import ABC, abstractmethod
from enum import Enum
import ui
from PyQt5.QtWidgets import QWidget, QApplication
import sys


class Client:
    def __init__(self, name: str):
        self.name = name
        self.steps: list["Step"] = []
        self.vars: dict[str, Any] = {}

    def add_step(self, step: "Step"):
        self.steps.append(step)

class StepType(Enum):
    SENDRECEIVE = 1
    COMPUTATION = 2
    SUBROUTINE = 3
    BROADCAST = 4
    INPUT = 5

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
    def handle(self, clients: list[Client]) -> list[str]:
        pass

    @abstractmethod
    def display_result(self, res: list[str]):
        pass

    def figureType(self) -> StepType:
        if isinstance(self, SendReceive):
            return StepType.SENDRECEIVE
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

class SendReceive(Step):
    def __init__(self, sender: Client, receiver: Client, vars: list[str]):
        super().__init__()
        self.sender = sender
        self.receiver = receiver
        self.vars = vars

    def __str__(self) -> str:
        return str(self.vars)

    def handle(self, clients: list[Client]):
        for var in self.vars:
            self.receiver.vars[var] = self.sender.vars[var]

        return [str(self.receiver.vars[v]) for v in self.vars]

    def display_result(self, res: list[str]):
        self.widget.display_result(res)


class Computation(Step):
    def __init__(self, var_name: str, computation: str):
        super().__init__()
        self.var_name = var_name
        self.computation = computation

    def __str__(self) -> str:
        return f"{self.var_name} = {self.computation}"

    def handle(self, clients: list[Client]):
        res: list[str] = []
        for client in clients:
            client.vars[self.var_name] = eval(self.computation, client.vars)
            res.append(str(client.vars[self.var_name]))
        return res

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

class Broadcast(Step):
    def __init__(self, party: Client, vars: list[str]):
        super().__init__()
        self.party = party
        self.vars = vars

    def __str__(self) -> str:
        return str(self.vars)

    def handle(self, clients: list[Client]):
        for client in clients:
            for var in self.vars:
                client.vars[var] = self.party.vars[var]

        return [str(clients[0].vars[v]) for v in self.vars]

    def display_result(self, res: list[str]):
        self.widget.display_result(res)

class Subroutine(Step):
    def __init__(self, name: str, input_mapping: dict[str, dict[str, str]], output_mapping: dict[str, dict[str, str]]):
        super().__init__()
        self.name = name
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.steps: list[Step] = []

    def __str__(self) -> str:
        return f"Subroutine {self.name}"

    def handle(self, clients: list[Client]):
        for step in self.steps:
            step.handle(clients)

        return []

    def display_result(self, res: list[str]):
        pass

class Input(Step):
    def __init__(self, var_name: str, var_type: type):
        super().__init__()
        self.var_name = var_name
        self.var_type = var_type

    def __str__(self) -> str:
        return self.var_name

    def handle(self, clients: list[Client]):
        inputs: list[Any] = self.widget.get_inputs()
        for i, client in enumerate(clients):
            client.vars[self.var_name] = self.var_type(inputs[i])

        return []

    def display_result(self, res: list[str]):
        pass


class SMPCvisualiser():
    def __init__(self, parties: list[str]):
        self.app = QApplication(sys.argv)
        self.gui = ui.MainWindow(parties, self.one_step, self.run, self.reset)
        self.party_names = parties
        self.parties: dict[str, Client] = {party: Client(party) for party in parties}

        self.steps: list[Step] = []
        self.subroutine_stack: list[Subroutine] = []

        self.step_index = 0

    def run_gui(self):
        self.gui.show()
        sys.exit(self.app.exec_())

    def one_step(self):
        if self.step_index < len(self.steps):
            res = self.steps[self.step_index].handle(list(self.parties.values()))
            self.steps[self.step_index].display_result(res)
            self.step_index += 1

    def run(self):
        for step in self.steps[self.step_index:]:
            res = step.handle(list(self.parties.values()))
            step.display_result(res)

        self.step_index = len(self.steps)

    def reset(self):
        for party in self.parties.values():
            party.steps = []
            party.vars = {}

        for step in self.steps:
            step.widget.reset()

        self.step_index = 0

    def add_input(self, var_name: str, var_type: type = int):
        inst = Input(var_name, var_type)
        widget = self.gui.add_input_step(var_name)
        inst.widget = widget
        self.steps.append(inst)

    def add_computation(self, new_var_name: str, computation: str):
        inst = Computation(new_var_name, computation)
        widget = self.gui.add_computation_step(f"{new_var_name} = {computation}")
        inst.widget = widget
        self.steps.append(inst)

    def send_message(self, sending_party_name: str, receiving_party_name: str, variables: list[str]):
        inst = SendReceive(self.parties[sending_party_name], self.parties[receiving_party_name], variables)
        sending = list(self.parties.keys()).index(sending_party_name)
        receiving = list(self.parties.keys()).index(receiving_party_name)
        widget = self.gui.add_send_step(sending, receiving, variables, variables)  #! Variables can be different on the other side
        inst.widget = widget
        self.steps.append(inst)

    def broadcast_variable(self, sending_party_name, variables: list[str]):
        inst = Broadcast(self.parties[sending_party_name], variables)
        widget = self.gui.add_broadcast_step(sending_party_name, variables)
        inst.widget = widget
        self.steps.append(inst)

    def start_subroutine(self, subroutine_name, input_mapping: dict[str, dict[str, str]], output_mapping: dict[str, dict[str, str]]):
        subroutine = Subroutine(subroutine_name, input_mapping, output_mapping)
        self.subroutine_stack.append(subroutine)

    def end_subroutine(self):
        self.subroutine_stack.pop()

v = SMPCvisualiser(["Alice", "Bob", "Charlie"])
v.add_input("a")
v.add_input("b")
v.add_computation("c", "a + b")
v.add_computation("b", "2")
v.send_message("Alice", "Bob", ["a", "b"])
v.send_message("Charlie", "Bob", ["a", "b"])
v.broadcast_variable("Bob", ["a", "b"])

v.run_gui()
