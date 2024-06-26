from typing import Any, Callable
from SMPCbox.gui import ui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
from SMPCbox.AbstractProtocol import AbstractProtocol
from SMPCbox.ProtocolParty import ProtocolParty
from multiprocessing import Process, Queue
from enum import Enum
import inspect
from SMPCbox.api import Step, ProtocolSide
import signal
from .constants import TIMER_INTERVAL, NoDefault


class Input:
    def __init__(self, var_names: list[str], var_types: list[type]):
        self.var_names = var_names
        self.var_types = var_types

    def get_inputs(self):
        inputs = self.widget.get_inputs()

        res: list[tuple[str, Any] | None] = []

        for inp, type_ in zip(inputs, self.var_types):
            if inp is None:
                res.append(None)
            else:
                res.append((inp[0], type_(inp[1])))

        return res

    def create_widget(self, gui: ui.MainWindow):
        self.widget = gui.add_input_step(self.var_names)


class Subroutine:
    def __init__(
        self,
        name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        self.name = name
        self.party_mapping = party_mapping
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.steps: list[tuple[Step, tuple]] = []

        self.gui: ui.SubroutineWindow | None = None

    def __repr__(self):
        return f"Subroutine {self.name}"

    def add_step(self, step: Step, args: tuple):
        self.steps.append((step, args))

        if self.gui:
            self.handle_step((step, args))

    def on_close(self):
        self.gui = None

    def show(self):
        if self.gui:
            return

        parties = [self.party_mapping[party] for party in self.party_mapping]
        self.gui = ui.SubroutineWindow(self.name, parties, self.on_close)
        self.gui.show()

        for step in self.steps:
            self.handle_step(step)

    def handle_step(self, step: tuple[Step, tuple]):
        if not self.gui:
            return
        try:
            step_type, args = step
            if step_type == Step.COMMENT:
                self.gui.add_comment(args[0])
            elif step_type == Step.COMPUTATION:
                self.gui.add_computation_step(*args)
            elif step_type == Step.SEND:
                self.gui.add_send_step(*args)
            elif step_type == Step.BROADCAST:
                self.gui.add_broadcast_step(*args)
            elif step_type == Step.SUBROUTINE:
                self.gui.add_subroutine_step(*args)
            elif step_type == Step.END_SUBROUTINE:
                self.gui.add_end_subroutine_step(*args)
            elif step_type == Step.END_PROTOCOL:
                ...
            else:
                raise ValueError(f"Unknown step type: {step_type}")
        except Exception as e:
            print(e)


class State(Enum):
    NOT_STARTED = 0
    PAUSED = 1
    RUNNING = 2
    ONE_STEP = 3
    FINISHED = 4


class Protocolvisualiser(ProtocolSide):
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.protocols: dict[str, type[AbstractProtocol]] = {}
        self.protocol_name: str = ""
        self.protocol: AbstractProtocol | None = None
        self.party_names: list[str] = []
        self.gui = ui.MainWindow(
            self.party_names, self.one_step, self.run, self.reset, self.on_close
        )
        self.gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)
        self.parties: dict[str, ProtocolParty] = {
            party: ProtocolParty(party) for party in self.party_names
        }

        self.running_protocol: Process | None = None
        self.queue: Queue

        self.set_status(State.NOT_STARTED)

        self.one_step_timer: QTimer | None = None
        self.running_timer: QTimer | None = None

        self.inputs: list[Input] = []
        self.subroutine_stack: list[Subroutine] = []

        self.atexit: list[Callable] = []

    def set_status(self, status: State):
        string = status.name.replace("_", " ").capitalize()
        self.gui.set_status(string)

        self.state = status

    def setup_protocol(self):
        self.protocol_name = self.gui.protocol_chooser.currentText()
        self.gui.set_protocol_name(self.protocol_name)

        self.gui.update_party_names([])

        self.gui.list_widget.clear()

    def setup_input(self):
        if self.protocol is None:
            return

        self.party_names = self.protocol.get_party_names()
        self.parties = {party: ProtocolParty(party) for party in self.party_names}
        self.gui.update_party_names(self.party_names)
        inp = self.protocol.get_expected_input()

        self.inputs = []

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

    @staticmethod
    def run_protocol(protocol: AbstractProtocol, queue: Queue):
        """Starts a protocol and adds the visualizer. Is supposed to be run in a separate process.

        Args:
            protocol (AbstractProtocol): The protocol to run
            queue (Queue): The queue to send the steps to
        """
        protocol.set_protocol_visualiser(ProtocolSide(queue))

        def signal_handler(signal, frame):
            protocol.terminate_protocol()
            raise SystemExit

        signal.signal(signal.SIGTERM, signal_handler)

        protocol.run()

    def start_protocol(self):
        if self.protocol is None:
            return

        if self.running_protocol:
            self.running_protocol.terminate()

        input_dict: dict[str, dict[str, Any]] = {}

        for input in self.inputs:
            for party, inp in zip(self.party_names, input.get_inputs()):
                if inp is None:
                    continue

                prompt, result = inp

                if party not in input_dict:
                    input_dict[party] = {}

                input_dict[party][prompt] = result

        self.protocol.set_input(input_dict)

        self.queue = Queue()

        self.running_protocol = Process(
            target=self.run_protocol, args=(self.protocol, self.queue)
        )
        self.running_protocol.start()

    def run_gui(self):
        self.gui.show()
        sys.exit(self.app.exec_())

    def check_queue(self):
        try:
            step = self.queue.get(block=False)
            self.handle_step(step)

            if self.one_step_timer and not self.subroutine_stack:
                self.one_step_timer.stop()
                self.one_step_timer = None
                self.set_status(State.PAUSED)
                self.gui.set_paused()
        except Exception:
            pass

    def one_step(self):
        if self.state == State.NOT_STARTED:
            self.start_protocol()

        self.set_status(State.ONE_STEP)
        self.gui.start_one_step()
        self.one_step_timer = QTimer()
        self.one_step_timer.timeout.connect(self.check_queue)
        self.one_step_timer.start(TIMER_INTERVAL)

    def run(self):
        def start_running():
            self.set_status(State.RUNNING)
            self.running_timer = QTimer()
            self.running_timer.timeout.connect(self.check_queue)
            self.running_timer.start(TIMER_INTERVAL)
            self.gui.set_running()

        if self.state == State.NOT_STARTED:
            self.start_protocol()
            start_running()

        elif self.state == State.PAUSED:
            start_running()

        elif self.state == State.RUNNING:
            self.set_status(State.PAUSED)
            if self.running_timer:
                self.running_timer.stop()
            self.running_timer = None
            self.gui.set_paused()

        elif self.state == State.ONE_STEP:
            if self.one_step_timer:
                self.one_step_timer.stop()
            self.one_step_timer = None

            start_running()

    def reset(self):
        self.set_status(State.NOT_STARTED)

        if self.running_protocol:
            self.running_protocol.terminate()
            self.running_protocol = None

        if self.one_step_timer:
            self.one_step_timer.stop()
            self.one_step_timer = None

        if self.running_timer:
            self.running_timer.stop()
            self.running_timer = None

        self.gui.set_paused()
        self.setup_protocol()
        self.setup_input()

    def handle_step(self, step: tuple[Step, tuple]):
        step_type, args = step
        if step_type == Step.COMMENT:
            self.add_comment(args[0])
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
        elif step_type == Step.END_PROTOCOL:
            self.end_protocol()
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    def add_comment(self, comment: str):
        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(Step.COMMENT, (comment,))
        else:
            self.gui.add_comment(comment)

    def add_input(self, var_names: list[str], var_type: list[type]) -> None:
        inst = Input(var_names, var_type)
        inst.create_widget(self.gui)
        self.inputs.append(inst)

    @staticmethod
    def eclipse(value: Any, length: int = 10) -> str:
        value = str(value)
        if len(value) > length:
            return value[: length - 3] + "..."
        return value

    def add_computation(
        self,
        party_name: str,
        computed_vars: dict[str, Any],
        computation: str,
    ):
        result = ", ".join(self.eclipse(value) for value in (computed_vars.values()))

        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(
                Step.COMPUTATION,
                (
                    party_name,
                    f"{', '.join(computed_vars.keys())} = {computation}",
                    result,
                ),
            )
        else:
            self.gui.add_computation_step(
                party_name,
                f"{', '.join(computed_vars.keys())} = {computation}",
                result,
            )

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        for var in variables:
            variables[var] = self.eclipse(variables[var])

        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(
                Step.SEND, (sending_party_name, receiving_party_name, variables)
            )
        else:
            self.gui.add_send_step(sending_party_name, receiving_party_name, variables)

    def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
        variables_list = list(variables.keys())

        for var in variables:
            variables[var] = self.eclipse(variables[var])

        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(
                Step.BROADCAST, (party_name, variables_list)
            )
        else:
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

        subroutine_object = Subroutine(subroutine_name, party_mapping, input_mapping, output_mapping)

        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(
                Step.SUBROUTINE,
                (subroutine_name, clients, subroutine_object),
            )
        else:
            self.gui.add_subroutine_step(subroutine_name, clients, subroutine_object)

        self.subroutine_stack.append(
            subroutine_object
        )

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        self.subroutine_stack.pop()

        if self.subroutine_stack:
            self.subroutine_stack.pop().add_step(Step.END_SUBROUTINE, (output_values,))
        else:
            self.gui.add_end_subroutine_step(output_values)

    def end_protocol(self):
        self.set_status(State.FINISHED)
        self.gui.set_finished()

    @staticmethod
    def get_function_params(func: Callable) -> dict[str, dict[str, Any]]:
        signature = inspect.signature(func)
        params = {}
        for name, param in signature.parameters.items():
            param_info = {
                "type": (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else None
                ),
                "default": (
                    param.default
                    if param.default != inspect.Parameter.empty
                    else NoDefault
                ),
            }
            params[name] = param_info
        return params

    def start_protocol_with_arguments(
        self, protocol_class: type["AbstractProtocol"], kwargs: dict[str, Any]
    ):
        self.protocol = protocol_class(**kwargs)
        self.reset()

    def choose_protocol(self, protocol_class: type["AbstractProtocol"]):
        params = self.get_function_params(protocol_class.__init__)
        del params["self"]

        if params:
            self.protocol = None
            self.gui.get_starting_values(
                params,
                lambda kwargs: self.start_protocol_with_arguments(
                    protocol_class, kwargs
                ),
            )
            self.reset()
        else:
            self.gui.protocol_input_list.clear()
            self.protocol = protocol_class()
            self.reset()

    def set_protocols(self, protocols: dict[str, type[AbstractProtocol]]):
        print("Setting protocols")
        self.protocols = protocols
        self.gui.protocol_chooser.clear()
        self.gui.protocol_chooser.addItems(list(protocols.keys()))

        # if self.protocol_name:
        #     self.gui.protocol_chooser.setCurrentText(self.protocol_name)
        #     self.choose_protocol(self.protocols[self.protocol_name])
        # else:
        #     self.choose_protocol(
        #         list(protocols.values())[self.gui.protocol_chooser.currentIndex()]
        #     )

    def protocol_changed(self, index: int):
        self.choose_protocol(list(self.protocols.values())[index])

    def on_close(self):
        if self.running_protocol:
            self.running_protocol.terminate()

        for func in self.atexit:
            func()

    def add_atexit(self, func: Callable):
        self.atexit.append(func)