from typing import Any
from SMPCbox.gui import ui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor
import sys
from SMPCbox.AbstractProtocol import AbstractProtocol, AbstractProtocolVisualiser
from SMPCbox.ProtocolCompiler import CompiledProtocol, Step
from SMPCbox.ProtocolParty import ProtocolParty


class Protocolvisualiser(AbstractProtocolVisualiser):
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.protocols: dict[str, type[AbstractProtocol]] = {}
        self.protocol_name: str = ""
        self.protocol: AbstractProtocol | None = None
        self.compiled_protocol: CompiledProtocol | None = None
        self.party_names: list[str] = []
        self.gui = ui.MainWindow(self.party_names, self.one_step, self.run, self.reset)
        self.gui.protocol_chooser.currentIndexChanged.connect(self.protocol_changed)
        self.parties: dict[str, ProtocolParty] = {
            party: ProtocolParty(party) for party in self.party_names
        }

        self.steps: list[Step] = []

        self.step_index = 0

    def compile_protocol(self):
        if self.protocol is None:
            return

        self.gui.set_protocol_name(self.protocol.protocol_name)
        self.party_names = self.protocol.get_party_roles()
        self.parties = {party: ProtocolParty(party) for party in self.party_names}
        self.gui.update_party_names(self.party_names)
        inp = self.protocol.get_expected_input()

        self.gui.list_widget.clear()

        self.compiled_protocol = self.protocol.compile()
        self.steps = self.compiled_protocol.steps
        for step in self.steps:
            step.create_widget(self.gui)


        # inputs: list[list[str]] = []
        # for expected_vars in inp.values():
        #     for i, var in enumerate(expected_vars):
        #         if i >= len(inputs):
        #             inputs.append([])
        #         inputs[i].append(var)

        # max_len = max(len(i) for i in inputs)
        # for i in inputs:
        #     while len(i) < max_len:
        #         i.append("")

        # for i in inputs:
        #     self.add_input(i)

        # self.protocol.set_input(
        #     {
        #         party: {var: 0 for var in expected_vars}
        #         for party, expected_vars in inp.items()
        #     }
        # )

        # self.protocol.set_protocol_visualiser(self)
        # self.protocol.compile()

    def run_gui(self):
        self.gui.show()
        sys.exit(self.app.exec_())

    def one_step(self):
        if self.step_index < len(self.steps):
            for i, step in enumerate(self.steps):
                # Change the background color of the current step
                item = self.gui.list_widget.item(self.step_index)
                if item:
                    item.setBackground(QColor(155, 155, 133))

                if step is not None:
                    parties = list(self.parties.values())
                    res = step.handle(parties)

                self.step_index += 1

    def run(self):
        for step in self.steps[self.step_index :]:
            parties = list(self.parties.values())
            res = step.handle(parties)
            step.display_result(res)

        self.step_index = len(self.steps)

    def reset(self):
        for step in self.steps:
            step.widget.reset()

        self.step_index = 0

    # def add_step(self, step_name: str):
    #     self.gui.add_step(step_name)
    #     self.gui.update_all_indexes()

    # def add_input(self, var_names: list[str], var_type: type = int):
    #     inst = Input(var_names, var_type)
    #     widget = self.gui.add_input_step(var_names)
    #     inst.widget = widget
    #     self.steps.append(inst)

    # def add_computation(
    #     self,
    #     party_name: str,
    #     computed_vars: dict[str, Any],
    #     computation: str,
    #     used_vars: dict[str, Any],
    # ):
    #     inst = Computation(list(computed_vars.keys())[0], computation)
    #     widget = self.gui.add_computation_step(
    #         party_name, f"{list(computed_vars.keys())[0]} = {computation}"
    #     )
    #     inst.widget = widget
    #     self.steps.append(inst)

    # def send_message(
    #     self,
    #     sending_party_name: str,
    #     receiving_party_name: str,
    #     variables: list[str],
    # ):
    #     print(self.parties, sending_party_name, receiving_party_name)
    #     inst = SendReceive(
    #         self.parties[sending_party_name],
    #         self.parties[receiving_party_name],
    #         variables,
    #     )
    #     sending = list(self.parties.keys()).index(sending_party_name)
    #     receiving = list(self.parties.keys()).index(receiving_party_name)
    #     widget = self.gui.add_send_step(
    #         sending, receiving, variables, variables
    #     )  #! Variables can be different on the other side
    #     inst.widget = widget
    #     self.steps.append(inst)

    # def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
    #     variables_list = list(variables.keys())
    #     inst = Broadcast(self.parties[party_name], variables_list)
    #     widget = self.gui.add_broadcast_step(party_name, variables_list)
    #     inst.widget = widget
    #     self.steps.append(inst)

    # def start_subroutine(
    #     self,
    #     subroutine_name: str,
    #     party_mapping: dict[str, str],
    #     input_mapping: dict[str, dict[str, str]],
    #     output_mapping: dict[str, dict[str, str]],
    # ):
    #     inst = Subroutine(subroutine_name, party_mapping, input_mapping, output_mapping)
    #     clients = []
    #     for party_name in self.party_names:
    #         if party_name in party_mapping:
    #             clients.append(party_mapping[party_name])
    #         else:
    #             clients.append("")

    #     widget = self.gui.add_subroutine_step(subroutine_name, clients)
    #     inst.widget = widget
    #     self.steps.append(inst)

    # def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
    #     pass

    def set_protocols(self, protocols: dict[str, type[AbstractProtocol]]):
        self.protocols = protocols
        self.gui.protocol_chooser.clear()
        self.gui.protocol_chooser.addItems(list(protocols.keys()))

        if self.protocol_name:
            self.gui.protocol_chooser.setCurrentText(self.protocol_name)
            self.protocol = self.protocols[self.protocol_name]()
        else:
            self.protocol = list(protocols.values())[
                self.gui.protocol_chooser.currentIndex()
            ]()

        self.compile_protocol()

    def protocol_changed(self, index: int):
        self.protocol = list(self.protocols.values())[index]()
        self.compile_protocol()
