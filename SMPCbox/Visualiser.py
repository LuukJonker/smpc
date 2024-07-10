from typing import Any, Callable
from SMPCbox.gui import ui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
from SMPCbox.AbstractProtocol import AbstractProtocol
from SMPCbox.ProtocolParty import ProtocolParty
from multiprocessing import Process, Queue, Event
from enum import Enum
import inspect
from SMPCbox.CommunicationLayer import Step, ProtocolSide
import signal
from .constants import TIMER_INTERVAL, NoDefault, QUEUE_SIZE
from SMPCbox.Lobby import PeerLobby, Host, Peer


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

        inputs: list[list[str]] = []
        defaults: list[list[Any]] = []
        for party_index, expected_vars in enumerate(self.input_mapping.values()):
            for var_index, (var, value) in enumerate(expected_vars.items()):
                if len(inputs) <= var_index:
                    inputs.append([""] * len(self.party_mapping))
                if len(defaults) <= var_index:
                    defaults.append([None] * len(self.party_mapping))

                inputs[var_index][party_index] = var
                defaults[var_index][party_index] = value

        for default, inp in zip(defaults, inputs):
            self.gui.add_input_step(inp, default, mutable=False)

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


class ProtocolVisualizer(ProtocolSide):
    def __init__(self, distributed = False):
        self.app = QApplication(sys.argv)
        self.protocols: dict[str, type[AbstractProtocol]] = {}
        self.protocol_name: str = ""
        self.protocol: AbstractProtocol | None = None
        self.party_names: list[str] = []
        self.gui: ui.MainWindow | ui.ParticipantWindow
        if not distributed:
            self.gui = ui.MainWindow(self.party_names, self.one_step, self.run, self.reset, self.on_close)
            self.gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)

        self.parties: dict[str, ProtocolParty] = {
            party: ProtocolParty(party) for party in self.party_names
        }

        self.state: State = State.NOT_STARTED

        self.protocol_index: int | None = None
        self.is_protocols_being_set = Event()

        self.running_protocol: Process | None = None
        self.queue: Queue

        self.one_step_timer: QTimer | None = None
        self.running_timer: QTimer | None = None

        self.inputs: list[Input] = []
        self.subroutine_stack: list[Subroutine] = []

        self.atexit: list[Callable] = []

        self.distributed_setup: tuple[dict[str, str], str] | None = None

    def set_status(self, status: State):
        string = status.name.replace("_", " ").capitalize()
        self.gui.set_status(string)

        self.state = status

    def setup_protocol(self):
        self.protocol_name = self.gui.protocol_chooser.currentText()
        self.gui.set_protocol_name(self.protocol_name)

        self.gui.update_party_names([])

        self.gui.list_widget.clear()

    def setup_input(self, distributed_name: str | None = None):
        if self.protocol is None:
            return

        self.party_names = self.protocol.party_names()
        self.parties = {party: ProtocolParty(party) for party in self.party_names}
        self.gui.update_party_names(self.party_names)
        inp = self.protocol.input_variables()

        if len(inp) == 0:
            return

        self.inputs = []

        inputs: list[list[str]] = []
        for party_index, expected_vars in enumerate(inp.values()):
            for var_index, var in enumerate(expected_vars):
                if len(inputs) <= var_index:
                    inputs.append([""] * len(self.parties))
                if (
                    not distributed_name
                    or distributed_name == self.party_names[party_index]
                ):
                    inputs[var_index][party_index] = var

        max_len = max(len(i) for i in inputs)
        for i in inputs:
            while len(i) < max_len:
                i.append("")

        for i in inputs:
            self.add_input(i, [int for _ in i])

    @staticmethod
    def run_protocol(protocol: AbstractProtocol, queue: Queue, distributed_setup: tuple[dict[str, str], str] | None = None):
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

        if distributed_setup:
            protocol.set_party_addresses(*distributed_setup)

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

        self.queue = Queue(QUEUE_SIZE)

        self.running_protocol = Process(
            target=self.run_protocol, args=(self.protocol, self.queue, self.distributed_setup)
        )
        self.running_protocol.start()

    def run_gui(self):
        self.set_status(State.NOT_STARTED)
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

        if not self.distributed_setup:
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
            self.end_protocol(*args)
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

        subroutine_object = Subroutine(
            subroutine_name, party_mapping, input_mapping, output_mapping
        )

        if self.subroutine_stack:
            self.subroutine_stack[-1].add_step(
                Step.SUBROUTINE,
                (subroutine_name, clients, subroutine_object),
            )
        else:
            self.gui.add_subroutine_step(subroutine_name, clients, subroutine_object)

        self.subroutine_stack.append(subroutine_object)

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        self.subroutine_stack.pop()

        if self.subroutine_stack:
            self.subroutine_stack.pop().add_step(Step.END_SUBROUTINE, (output_values,))
        else:
            self.gui.add_end_subroutine_step(output_values)

    def end_protocol(self, party_statistics: dict[str, Any], protocol_statistics: Any):
        self.gui.add_statistics(party_statistics, protocol_statistics)
        self.set_status(State.FINISHED)
        self.gui.set_finished()

    @staticmethod
    def get_function_params(func: Callable) -> dict[str, dict[str, Any]]:
        signature = inspect.signature(func)
        params = {}
        for name, param in signature.parameters.items():
            param_type = param.annotation
            if param.annotation == inspect.Parameter.empty:
                if param.default == inspect.Parameter.empty:
                    param_type = int
                else:
                    param_type = type(param.default)

            param_info = {
                "type": (param_type),
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
        else:
            self.gui.protocol_input_list.clear()
            self.protocol = protocol_class()

        self.reset()

    def set_protocols(self, protocols: dict[str, type[AbstractProtocol]]):
        self.protocols = protocols
        self.is_protocols_being_set.set()
        self.gui.protocol_chooser.clear()
        self.gui.protocol_chooser.addItems(list(protocols.keys()))
        self.gui.protocol_chooser.setCurrentIndex(self.protocol_index or 0)

    def protocol_changed(self, index: int):
        if self.is_protocols_being_set.is_set():
            self.choose_protocol(list(self.protocols.values())[self.protocol_index or 0])
            self.is_protocols_being_set.clear()
        else:
            self.protocol_index = index
            self.choose_protocol(list(self.protocols.values())[index])

    def on_close(self):
        if self.running_protocol:
            self.running_protocol.terminate()

        for func in self.atexit:
            func()

    def add_atexit(self, func: Callable):
        self.atexit.append(func)


class DistributedVisualizer(ProtocolVisualizer):
    def __init__(self):
        super().__init__(True)

        self.gui = ui.ParticipantWindow("", [], self.on_ready, self.on_close)

        self.role = None
        self.lobby_gui = PeerLobby(self.on_role_selection, self.on_host_start, self.setup_distributed_protocol)
        self.lobby_gui.setup_signal.connect(self.setup_distributed_gui)
        self.lobby_gui.start_signal.connect(self.run)

        self.host_configuration_gui: ui.HostWindow | None = None
        self.configuration: dict[str, Any] = {}

        self.addresses_setup: tuple[dict[str, str], str] | None = None

    def run_gui(self):
        print("Running distributed visualizer")
        self.lobby_gui.show()
        sys.exit(self.app.exec_())

    def on_host_start(self):
        participants = list(self.lobby_gui.peers.values())
        participants.append(self.lobby_gui.get_host())
        self.host_configuration_gui = ui.HostWindow(participants, self.on_configured, self.on_host_window_close)

        self.host_configuration_gui.protocol_chooser.clear()
        self.host_configuration_gui.protocol_chooser.addItems(list(self.protocols.keys()))
        self.host_configuration_gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)

        self.protocol_changed(0)

        self.host_configuration_gui.show()

    def on_configured(self, mapping: dict[str, Peer]):
        if not isinstance(self.lobby_gui.client, Host):
            raise ValueError("Only the host can configure the protocol.")

        if not self.host_configuration_gui:
            return

        protocol_name = self.host_configuration_gui.protocol_chooser.currentText()
        self.lobby_gui.client.send_configuration(protocol_name, self.configuration, mapping)


    def on_host_window_close(self):
        self.host_configuration_gui = None

    def on_role_selection(self, role: str):
        self.role = role

    def set_protocols(self, protocols: dict[str, type[AbstractProtocol]]):
        self.protocols = protocols

        if self.host_configuration_gui:
            self.host_configuration_gui.protocol_chooser.clear()
            self.host_configuration_gui.protocol_chooser.addItems(list(protocols.keys()))

    def on_ready(self):
        self.lobby_gui.client.send_ready()

    def reset(self):
        if self.host_configuration_gui:
            if self.protocol:
                self.host_configuration_gui.update_parties(self.protocol.party_names())
            else:
                self.host_configuration_gui.update_parties([])


    def choose_protocol(self, protocol_class: type["AbstractProtocol"]):
        if not self.host_configuration_gui:
            return

        params = self.get_function_params(protocol_class.__init__)
        del params["self"]

        def on_start(kwargs: dict[str, Any]):
            self.configuration = kwargs
            self.start_protocol_with_arguments(protocol_class, kwargs)

        if params:
            self.protocol = None
            self.host_configuration_gui.update_parties([])
            self.host_configuration_gui.get_starting_values(
                params,
                on_start,
            )
        else:
            self.host_configuration_gui.protocol_input_list.clear()
            self.protocol = protocol_class()
            self.configuration = {}

        self.reset()

    def setup_distributed_protocol(self, protocol_name: str, party_name: str, addresses: dict[str, str], configuration: dict[str, Any]):
        self.protocol = self.protocols[protocol_name](**configuration)

        self.distributed_setup = (addresses, party_name)

        self.protocol_name = protocol_name
        self.lobby_gui.setup_signal.emit(party_name)

    def setup_distributed_gui(self, party_name: str):
        self.gui.set_protocol_name(self.protocol_name)

        self.gui.show()

        self.setup_input(party_name)

    def start_distributed_protocol(self):
        self.run()
