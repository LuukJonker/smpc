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
    QHBoxLayout,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QPainter, QPen, QColor
import math


class Section(QWidget):
    def __init__(self, text: str, extra_text: str = "", background_color="lightblue", border_color="blue"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{background-color: {background_color}; border: 2px solid {border_color}; border-radius: 5px;}}
            QLabel {{border: none; border-radius: 0px; text-align: center;}}
            """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 10, 40, 10)  # Add margins around the widget
        layout.setSpacing(40)  # Add spacing between elements

        self.frame = QFrame()
        self.label1 = QLabel(text)
        self.label1.setAlignment(Qt.AlignCenter)
        self.label2 = QLabel("")
        self.label2.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label1)

        if extra_text:
            extra_layout = QHBoxLayout()
            self.extra_frame = QFrame()
            self.extra_label = QLabel(extra_text)

            extra_layout.addWidget(self.extra_label)
            extra_layout.addWidget(self.label2)
            self.extra_frame.setLayout(extra_layout)
            layout.addWidget(self.extra_frame)

        else:
            layout.addWidget(self.label2)

        self.frame.setLayout(layout)

        frame_layout = QVBoxLayout()
        frame_layout.addWidget(self.frame)
        self.setLayout(frame_layout)

    def add_computation(self, text):
        self.label2.setText(text)


class Input(QWidget):
    def __init__(self, prompt: str):
        super().__init__()
        self.setStyleSheet(
            """
            QFrame {background-color: lightgrey; border: 2px solid grey; border-radius: 5px;}
            QLabel {border: none; border-radius: 0px; text-align: center;}
            """
        )

        layout = QHBoxLayout()
        # layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSpacing(20)

        self.frame = QFrame()
        self.prompt = QLabel(prompt)
        self.input = QLineEdit()

        layout.addWidget(self.prompt)
        layout.addWidget(self.input)
        self.frame.setLayout(layout)

        frame_layout = QVBoxLayout()
        frame_layout.addWidget(self.frame)
        self.setLayout(frame_layout)

    def get_input(self):
        return self.input.text()


class CalculationWidget(QWidget):
    def __init__(self, num_columns: int, calculation: str):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(50)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.sections = [Section(calculation) for _ in range(num_columns)]
        for i, column in enumerate(self.sections):
            layout.addWidget(column, 0, i)

        self.setLayout(layout)

    def display_result(self, results: list[str]):
        for i, result in enumerate(results):
            self.sections[i].label2.setText(result)

    def reset(self):
        for section in self.sections:
            section.label2.setText("")


class SendReceiveWidget(QWidget):
    def __init__(
        self,
        num_columns: int,
        sender: int,
        receiver: int,
        from_variables: list[str],
        to_variables: list[str],
    ):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(100)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        for i in range(num_columns):
            if i != sender and i != receiver:
                layout.addWidget(
                    Section("", background_color="none", border_color="none"), 0, i
                )

        self.send_section = Section(
            f"""Send\n{str(from_variables).replace("'", "")}""", background_color="lightgreen", border_color="green"
        )
        self.receive_section = Section(
            f"""Receive\n{str(to_variables).replace("'", "")}""", background_color="lightcoral", border_color="red"
        )
        layout.addWidget(self.send_section, 0, sender)
        layout.addWidget(self.receive_section, 0, receiver)

        self.setLayout(layout)

        self.sender_col = sender
        self.receiver_col = receiver
        self.num_columns = num_columns

    def display_result(self, results: list[str]):
        self.send_section.add_computation(str(results).replace("'", ""))
        self.receive_section.add_computation(str(results).replace("'", ""))

    def reset(self):
        self.send_section.label2.setText("")
        self.receive_section.label2.setText("")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor("black"))
        pen.setWidth(2)
        painter.setPen(pen)

        send_rect = self.send_section.geometry()
        receive_rect = self.receive_section.geometry()

        if self.sender_col < self.receiver_col:
            start_point = send_rect.topRight()
            end_point = receive_rect.topLeft()
        else:
            start_point = send_rect.topLeft()
            end_point = receive_rect.topRight()

        start_point.setY(start_point.y() + send_rect.height() // 2)
        end_point.setY(end_point.y() + receive_rect.height() // 2)

        painter.drawLine(start_point, end_point)

        angle = -math.atan2(
            end_point.y() - start_point.y(), end_point.x() - start_point.x()
        )

        arrow_head_size = 10
        arrow_p1 = end_point - QPoint(
            int(arrow_head_size * math.cos(angle + math.pi / 6)),
            int(arrow_head_size * math.sin(angle + math.pi / 6)),
        )
        arrow_p2 = end_point - QPoint(
            int(arrow_head_size * math.cos(angle - math.pi / 6)),
            int(arrow_head_size * math.sin(angle - math.pi / 6)),
        )

        painter.drawLine(end_point, arrow_p1)
        painter.drawLine(end_point, arrow_p2)


class BroadcastWidget(QWidget):
    def __init__(self, party_name: str, variables: list[str]):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setSpacing(20)  # Add spacing between elements

        self.section = Section(
            f"Broadcast from {party_name}",
            extra_text=str(variables).replace("'", ""),
            background_color="lightyellow",
            border_color="orange",
        )

        layout.addWidget(self.section)

        self.setLayout(layout)

    def display_result(self, results: list[str]):
        self.section.label2.setText(str(results).replace("'", ""))

    def reset(self):
        self.section.label2.setText("")


class InputWidget(QWidget):
    def __init__(self, num_columns: int, inputs: list[str]):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(100)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.inputs = [Input(inputs[i]) for i in range(num_columns)]
        for i, input in enumerate(self.inputs):
            layout.addWidget(input, 0, i)

        self.setLayout(layout)

    def get_inputs(self):
        return [input.get_input() for input in self.inputs]

    def reset(self):
        for input in self.inputs:
            input.input.setText("")


class MainWindow(QMainWindow):
    def __init__(
        self, parties: list[str], one_step_callback, run_callback, reset_callback
    ):
        super().__init__()
        self.setWindowTitle("SMPC Visualiser")

        self.resize(1000, 655)

        self.client_frame = QFrame()
        client_layout = QGridLayout()
        for i, party in enumerate(parties):
            client_layout.addWidget(QLabel(party), 0, i)
        self.client_frame.setLayout(client_layout)

        self.list_widget = QListWidget()

        self.one_step_button = QPushButton("One step")
        self.run_button = QPushButton("Run")
        self.reset_button = QPushButton("Reset")

        layout = QVBoxLayout()
        layout.addWidget(self.client_frame)
        layout.addWidget(self.list_widget)
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

    def add_input_step(self, prompt: str) -> InputWidget:
        widget = InputWidget(self.num_parties, [prompt] * self.num_parties)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)
        return widget

    def add_computation_step(self, calculation: str):
        widget = CalculationWidget(self.num_parties, calculation)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)
        return widget

    def add_send_step(
        self,
        sender: int,
        receiver: int,
        from_variables: list[str],
        to_variables: list[str],
    ):
        widget = SendReceiveWidget(
            self.num_parties, sender, receiver, from_variables, to_variables
        )
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)
        return widget

    def add_broadcast_step(self, party_name: str, variables: list[str]):
        widget = BroadcastWidget(party_name, variables)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)
        return widget
