from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QMainWindow,
    QFrame,
    QListWidget,
    QPushButton,
    QListWidgetItem,
    QComboBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCursor
from typing import Any, Callable
from SMPCbox.constants import NoDefault

from .comment import CommentWidget
from .input import InputWidget, Input
from .calculation import CalculationWidget
from .send_receive import SendReceiveWidget
from .broadcast import BroadcastWidget
from .subroutine import SubroutineWidget


class StyledButton(QPushButton):
    def __init__(self, text: str, parent=None, color_scheme="blue"):
        super().__init__(text, parent)
        self.color_scheme = color_scheme
        self.setStyleSheet(self.get_button_style())
        self.setCursor(QCursor(Qt.PointingHandCursor))  # type: ignore

    def get_button_style(self):
        color_schemes = {
            "blue": {
                "background": "#1E90FF",
                "hover": "#1C86EE",
                "pressed": "#1874CD",
                "disabled": "#87CEFA",
                "text": "white",
            },
            "green": {
                "background": "#32CD32",
                "hover": "#2E8B57",
                "pressed": "#228B22",
                "disabled": "#98FB98",
                "text": "white",
            },
            "red": {
                "background": "#FF6347",
                "hover": "#FF4500",
                "pressed": "#CD5C5C",
                "disabled": "#FFA07A",
                "text": "white",
            },
            "purple": {
                "background": "#9370DB",
                "hover": "#8A2BE2",
                "pressed": "#7B68EE",
                "disabled": "#DDA0DD",
                "text": "white",
            },
        }

        scheme = color_schemes[self.color_scheme]

        return f"""
        QPushButton {{
            background-color: {scheme["background"]};
            border: none;
            color: {scheme["text"]};
            padding: 10px 32px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            margin: 4px 2px;
            border-radius: 8px;
        }}
        QPushButton:disabled {{
            background-color: {scheme["disabled"]};
        }}
        QPushButton:hover {{
            background-color: {scheme["hover"]};
        }}
        QPushButton:pressed {{
            background-color: {scheme["pressed"]};
        }}
        """


class NoHighlightListWidget(QListWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(
            """
            QListWidget::item {
                background: transparent;
                border: none;
                color: black;
            }
            QListWidget::item:selected {
                background: transparent;
                color: black;
            }
        """
        )


class MainWindow(QMainWindow):
    def __init__(
        self,
        parties: list[str],
        one_step_callback: Callable,
        run_callback: Callable,
        reset_callback: Callable,
        on_close: Callable,
    ):
        super().__init__()
        self.setWindowTitle("SMPC Visualiser")

        self.resize(1000, 800)

        self.protocol_chooser = QComboBox()

        self.protocol_input_list = NoHighlightListWidget()
        self.protocol_input_list.setFixedHeight(100)

        self.client_frame = QFrame()
        self.client_layout = QGridLayout()
        for i, party in enumerate(parties):
            label = QLabel(party)
            label.setAlignment(Qt.AlignCenter)  # type: ignore
            self.client_layout.addWidget(label, 0, i)
        self.client_frame.setLayout(self.client_layout)

        self.list_widget = NoHighlightListWidget()
        self.list_widget.itemClicked.connect(self.on_item_click)

        self.status_label = QLabel("Status: Not started")

        self.one_step_button = StyledButton("One step", color_scheme="green")
        self.run_button = StyledButton("Run", color_scheme="blue")
        self.reset_button = StyledButton("Reset", color_scheme="red")

        self.on_close = on_close

        layout = QVBoxLayout()
        layout.addWidget(self.protocol_chooser)
        layout.addWidget(self.protocol_input_list)
        layout.addWidget(self.client_frame)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.status_label)
        layout.addWidget(self.one_step_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.reset_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.num_parties = len(parties)

        self.one_step_button.clicked.connect(one_step_callback)
        self.run_button.clicked.connect(run_callback)
        self.reset_button.clicked.connect(reset_callback)

        self.party_indexes = {party: 0 for party in parties}

    def closeEvent(self, a0):
        super().closeEvent(a0)
        self.on_close()

    def set_protocol_name(self, protocol_name: str):
        self.setWindowTitle(f"{protocol_name} - SMPC Visualiser")

    def set_status(self, status: str):
        self.status_label.setText(f"Status: {status}")

    def set_running(self):
        self.one_step_button.setEnabled(False)
        self.run_button.setText("Pause")
        self.run_button.setEnabled(True)
        self.reset_button.setEnabled(False)

    def set_paused(self):
        self.one_step_button.setEnabled(True)
        self.run_button.setText("Run")
        self.run_button.setEnabled(True)
        self.reset_button.setEnabled(True)

    def start_one_step(self):
        self.one_step_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def end_one_step(self):
        self.one_step_button.setEnabled(True)
        self.run_button.setEnabled(True)

    def set_finished(self):
        self.one_step_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.run_button.setText("Run")
        self.reset_button.setEnabled(True)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()

    def update_party_names(self, parties: list[str]):
        self.clear_layout(self.client_frame.layout())

        for i, party in enumerate(parties):
            label = QLabel(party)
            label.setAlignment(Qt.AlignCenter)  # type: ignore
            self.client_layout.addWidget(label, 0, i)

        self.num_parties = len(parties)
        self.party_indexes = {party: 0 for party in parties}

    def get_starting_values(self, kwargs: dict[str, Any], callback: Callable):
        input_widgets: list[Input] = []

        def on_change(display_error: bool = True):
            input_map = {widget.prompt: widget for widget in input_widgets}
            values = {}

            for key, value in kwargs.items():
                input_widget = input_map[key]
                try:
                    type_ = value["type"]
                    values[key] = type_(input_widget.get_input())
                except ValueError as e:
                    if display_error:
                        input_widget.display_error(str(e))
                    return

                input_widget.display_error("")

            callback(values)

        self.protocol_input_list.clear()

        for key, value in kwargs.items():
            # Create inputs for each key-value pair
            widget = Input(key)
            default = value["default"]
            if default is not None and default is not NoDefault:
                widget.set_input(str(default))
            widget.on_change(on_change)
            input_widgets.append(widget)
            list_item = QListWidgetItem(self.protocol_input_list)
            list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
            self.protocol_input_list.setItemWidget(list_item, widget)

        on_change(False)

    def on_item_click(self, item: QListWidgetItem):
        widget = self.list_widget.itemWidget(item)
        if isinstance(widget, SubroutineWidget):
            widget.on_click()

    def add_comment(self, comment: str) -> CommentWidget:
        widget = CommentWidget(comment)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_input_step(self, prompts: list[str]) -> InputWidget:
        widget = InputWidget(prompts)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_computation_step(self, party_name: str, calculation: str, result: str):
        index = self.party_indexes[party_name]

        item = self.list_widget.item(index)
        widget = self.list_widget.itemWidget(item)

        if widget is None:
            calculations = ["" for _ in range(self.num_parties)]
            calculations[self.get_party_index(party_name)] = calculation
            widget = CalculationWidget(calculations)
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
            self.list_widget.setItemWidget(list_item, widget)
        else:
            widget.update_calculation(self.get_party_index(party_name), calculation)

        widget.update_result(self.get_party_index(party_name), result)

        self.party_indexes[party_name] += 1

        return widget

    def add_send_step(
        self,
        sender: str,
        receiver: str,
        variables: dict[str, Any],
    ):
        sender_pos = self.get_party_index(sender)
        receiver_pos = self.get_party_index(receiver)

        widget = SendReceiveWidget(
            self.num_parties, sender_pos, receiver_pos, variables
        )
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_broadcast_step(self, party_name: str, variables: list[str]):
        widget = BroadcastWidget(party_name, variables)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_subroutine_step(self, subroutine_name: str, clients: list[str], subroutine_object: object):
        widget = SubroutineWidget(subroutine_name, clients, subroutine_object)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_end_subroutine_step(self, output_values: dict[str, dict[str, str]]):
        indexes = list(self.party_indexes.values())
        index = indexes[0]

        # Check if all indexes are the same.
        if all(i == index for i in indexes):
            item = self.list_widget.item(index - 1)
            widget = self.list_widget.itemWidget(item)
            if widget is None:
                raise ValueError("End of subroutine called without a widget.")

            if not isinstance(widget, SubroutineWidget):
                raise ValueError(
                    "End of subroutine called without a subroutine widget."
                )

            widget.display_result(output_values)
        else:
            raise ValueError(
                "The indexes of the parties are not the same with a call to end_subroutine."
            )

    def get_party_index(self, party_name: str):
        return list(self.party_indexes.keys()).index(party_name)

    def update_all_indexes(self):
        highest_index = max(self.party_indexes.values())
        for party in self.party_indexes:
            self.party_indexes[party] = highest_index + 1

class SubroutineWindow(MainWindow):
    def __init__(
        self,
        name: str,
        parties: list[str],
        on_close: Callable,
    ):
        super().__init__(parties, lambda: None, lambda: None, lambda: None, on_close)

        self.setWindowTitle(f"SMPC Visualiser - {name}")

        self.protocol_chooser.hide()
        self.protocol_input_list.hide()
        self.status_label.hide()
        self.one_step_button.hide()
        self.run_button.hide()
        self.reset_button.hide()
