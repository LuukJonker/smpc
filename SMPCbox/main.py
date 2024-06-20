from typing import Any
from SMPCbox.gui import ui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
from SMPCbox.AbstractProtocol import AbstractProtocol, AbstractProtocolVisualiser
from SMPCbox.ProtocolParty import ProtocolParty
from multiprocessing import Process, Queue
from enum import Enum
import re
from inspect import signature

TIMER_INTERVAL = 10


def replace_variables(expression: str, variables: dict[str, Any]):
    # Regular expression to match variable names
    variable_pattern = re.compile(r"\b[a-zA-Z_]\w*\b")

    # Function to replace a match with its corresponding value from the dictionary
    def variable_replacer(match: re.Match[str]):
        var_name = match.group(0)
        return str(variables.get(var_name, var_name))

    # Replace all variables in the expression using the replacer function
    result = variable_pattern.sub(variable_replacer, expression)

    return result


class Input:
    def __init__(self, var_names: list[str], var_types: list[type]):
        self.var_names = var_names
        self.var_types = var_types

    def get_inputs(self):
        results = self.widget.get_inputs()

        return {name: type_(result) for type_, (name, result) in zip(self.var_types, results.items())}

    def create_widget(self, gui: ui.MainWindow):
        self.widget = gui.add_input_step(self.var_names)


class Step(Enum):
    COMMENT = 1
    COMPUTATION = 2
    SEND = 3
    BROADCAST = 4
    SUBROUTINE = 5
    END_SUBROUTINE = 6


class ProtocolSide(AbstractProtocolVisualiser):
    def __init__(self, queue: Queue):
        self.queue = queue

    def add_step(self, step_name: str):
        self.queue.put((Step.COMMENT, (step_name,)))

    def add_computation(
        self,
        party_name: str,
        computed_vars: dict[str, Any],
        computation: str,
    ):
        print("put it on the queue")
        self.queue.put(
            (Step.COMPUTATION, (party_name, computed_vars, computation))
        )

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        self.queue.put(
            (Step.SEND, (sending_party_name, receiving_party_name, variables))
        )

    def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
        self.queue.put((Step.BROADCAST, (party_name, variables)))

    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        self.queue.put(
            (
                Step.SUBROUTINE,
                (subroutine_name, party_mapping, input_mapping, output_mapping),
            )
        )

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        self.queue.put((Step.END_SUBROUTINE, (output_values,)))


class State(Enum):
    NOT_STARTED = 0
    PAUSED = 1
    RUNNING = 2
    ONE_STEP = 3
    FINISHED = 4


def run_protocol(protocol: AbstractProtocol, queue: Queue):
    """Starts a protocol and adds the visualizer. Is supposed to be run in a separate process.

    Args:
        protocol (AbstractProtocol): The protocol to run
        queue (Queue): The queue to send the steps to
    """
    print("RUNNING PROTOCOL")
    protocol.set_protocol_visualiser(ProtocolSide(queue))
    protocol()


class Protocolvisualiser:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.protocols: dict[str, type[AbstractProtocol]] = {}
        self.protocol_name: str = ""
        self.protocol: AbstractProtocol | None = None
        self.party_names: list[str] = []
        self.gui = ui.MainWindow(self.party_names, self.one_step, self.run, self.reset)
        self.gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)
        self.parties: dict[str, ProtocolParty] = {
            party: ProtocolParty(party) for party in self.party_names
        }

        self.running_protocol: Process | None = None
        self.queue: Queue

        self.state = State.NOT_STARTED

        self.one_step_timer: QTimer | None = None
        self.running_timer: QTimer | None = None

        self.inputs: list[Input] = []

    def setup_input(self):
        if self.protocol is None:
            return

        self.protocol_name = self.gui.protocol_chooser.currentText()

        self.gui.set_protocol_name(self.protocol.protocol_name)
        self.party_names = self.protocol.party_names()
        self.parties = {party: ProtocolParty(party) for party in self.party_names}
        self.gui.update_party_names(self.party_names)
        inp = self.protocol.input_variables()

        self.gui.list_widget.clear()

        if len(inp) == 0:
            return

        inputs: list[list[str]] = []
        for i, expected_vars in enumerate(inp.values()):
            for i, var in enumerate(expected_vars):
                if i >= len(inputs):
                    inputs.append([])
                inputs[i].append(var)

        max_len = max(len(i) for i in inputs)
        for i in inputs:
            while len(i) < max_len:
                i.append("")

        for i in inputs:
            self.add_input(i, [int for _ in i])

    def start_protocol(self):
        if self.protocol is None:
            return

        if self.running_protocol:
            self.running_protocol.terminate()

        input_dict: dict[str, dict[str, Any]] = {}

        for inp in self.inputs:
            for party, (prompt, result) in zip(
                self.party_names, inp.get_inputs().items()
            ):
                if prompt is None or result is None:
                    continue

                if party not in input_dict:
                    input_dict[party] = {}

                input_dict[party][prompt] = result

        self.protocol.set_input(input_dict)

        self.queue = Queue()

        self.running_protocol = Process(
            target=run_protocol, args=(self.protocol, self.queue)
        )
        self.running_protocol.start()

    def run_gui(self):
        self.gui.show()
        sys.exit(self.app.exec_())

    def check_queue(self):
        try:
            step = self.queue.get(block=False)
            self.handle_step(step)
            if self.one_step_timer:
                self.one_step_timer.stop()
                self.one_step_timer = None
                self.state = State.PAUSED
        except Exception:
            pass

    def one_step(self):
        if self.state == State.NOT_STARTED:
            self.start_protocol()

        self.state = State.ONE_STEP
        self.one_step_timer = QTimer()
        self.one_step_timer.timeout.connect(self.check_queue)
        self.one_step_timer.start(TIMER_INTERVAL)

    def run(self):
        if self.state == State.NOT_STARTED:
            self.start_protocol()
            self.state = State.RUNNING
            self.running_timer = QTimer()
            self.running_timer.timeout.connect(self.check_queue)
            self.running_timer.start(TIMER_INTERVAL)
            self.gui.set_running()

        elif self.state == State.PAUSED:
            self.state = State.RUNNING
            self.running_timer = QTimer()
            self.running_timer.timeout.connect(self.check_queue)
            self.running_timer.start(TIMER_INTERVAL)
            self.gui.set_running()

        elif self.state == State.RUNNING:
            self.state = State.PAUSED
            if self.running_timer:
                self.running_timer.stop()
            self.running_timer = None
            self.gui.set_paused()

    def reset(self):
        self.setup_input()
        self.state = State.NOT_STARTED

        if self.running_protocol:
            self.running_protocol.terminate()
            self.running_protocol = None

        if self.one_step_timer:
            self.one_step_timer.stop()
            self.one_step_timer = None

        if self.running_timer:
            self.running_timer.stop()
            self.running_timer = None

    def handle_step(self, step: tuple[Step, tuple]):
        step_type, args = step
        if step_type == Step.COMMENT:
            self.add_step(args[0])
        elif step_type == Step.COMPUTATION:
            self.add_computation(*args)
        elif step_type == Step.SEND:
            self.send_message(*args)
        elif step_type == Step.BROADCAST:
            self.broadcast_variable(*args)
        elif step_type == Step.SUBROUTINE:
            self.start_subroutine(*args)
        elif step_type == Step.END_SUBROUTINE:
            self.end_subroutine(*args)

    def add_step(self, step_name: str):
        self.gui.add_comment(step_name)

    def add_input(self, var_names: list[str], var_type: list[type]) -> None:
        inst = Input(var_names, var_type)
        inst.create_widget(self.gui)
        self.inputs.append(inst)

    def add_computation(
        self,
        party_name: str,
        computed_vars: dict[str, Any],
        computation: str,
        used_vars: dict[str, Any],
    ):
        self.gui.add_computation_step(
            party_name,
            f"{list(computed_vars.keys())[0]} = {computation}",
            f"{list(computed_vars.values())[0]} = {replace_variables(computation, used_vars)}",
        )

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        self.gui.add_send_step(
            sending_party_name, receiving_party_name, list(variables.keys()), list(variables.keys())
        )

    def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
        variables_list = list(variables.keys())
        self.gui.add_broadcast_step(party_name, variables_list)

    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        clients = []
        for party_name in self.party_names:
            if party_name in party_mapping:
                clients.append(party_mapping[party_name])
            else:
                clients.append("")

        self.gui.add_subroutine_step(subroutine_name, clients)

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        self.gui.add_end_subroutine_step(output_values)

    def choose_protocol(self, protocol_class: type['AbstractProtocol']):
        sig = signature(protocol_class.__init__)
        params = sig.parameters
        params = {name: param.annotation for name, param in params.items()}
        print(params)


    def set_protocols(self, protocols: dict[str, type[AbstractProtocol]]):
        self.protocols = protocols
        self.gui.protocol_chooser.currentIndexChanged.disconnect()
        self.gui.protocol_chooser.clear()
        self.gui.protocol_chooser.addItems(list(protocols.keys()))

        if self.protocol_name:
            self.gui.protocol_chooser.setCurrentText(self.protocol_name)
            self.protocol = self.protocols[self.protocol_name]()
        else:
            self.protocol = list(protocols.values())[
                self.gui.protocol_chooser.currentIndex()
            ]()

        self.gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)

        self.reset()

    def protocol_changed(self, index: int):
        self.choose_protocol(list(self.protocols.values())[index])
        self.reset()