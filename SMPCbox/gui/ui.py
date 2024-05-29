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
    QComboBox,
)
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
import math


class Section(QWidget):
    def __init__(
        self,
        text: str,
        extra_text: str = "",
        background_color="lightblue",
        border_color="blue",
    ):
        super().__init__()

        self.text = text
        self.extra_text = extra_text
        self.background_color = background_color
        self.border_color = border_color

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
        self.label1.setAlignment(Qt.AlignCenter)  # type: ignore
        self.label2 = QLabel("")
        self.label2.setAlignment(Qt.AlignCenter)  # type: ignore
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
        self.extra_text = text
        self.label2.setText(text)

    def disappear(self):
        self.setStyleSheet("")

    def reappear(self):
        self.setStyleSheet(
            f"""
            QFrame {{background-color: {self.background_color}; border: 2px solid {self.border_color}; border-radius: 5px;}}
            QLabel {{border: none; border-radius: 0px; text-align: center;}}
            """
        )


class Input(QWidget):
    def __init__(self, prompt: str, background_color="lightgrey", border_color="grey"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{background-color: {background_color}; border: 2px solid {border_color}; border-radius: 5px;}}
            QLabel {{border: none; border-radius: 0px; text-align: center;}}
            """
        )

        if prompt == "":
            self.setStyleSheet("opacity: 0; color: white; border: none; background-color: none;")

        layout = QHBoxLayout()

        self.frame = QFrame()
        self.prompt = QLabel(f"{prompt}: ")
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
    def __init__(self, calculations: list[str]):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(50)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.sections = [Section(calculation) for calculation in calculations]
        for i, column in enumerate(self.sections):
            layout.addWidget(column, 0, i)

            if column.label1.text() == "":
                column.disappear()

        self.setLayout(layout)

    def display_result(self, results: list[str]):
        for i, result in enumerate(results):
            self.sections[i].label2.setText(result)

    def reset(self):
        for section in self.sections:
            section.label2.setText("")

    def update_calculation(self, index: int, calculation: str):
        self.sections[index].label1.setText(calculation)
        self.sections[index].reappear()


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
            f"""Send\n{str(from_variables).replace("'", "")}""",
            background_color="lightgreen",
            border_color="green",
        )
        self.receive_section = Section(
            f"""Receive\n{str(to_variables).replace("'", "")}""",
            background_color="lightcoral",
            border_color="red",
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

    def paintEvent(self, a0):
        super().paintEvent(a0)
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


class SubroutineWidget(QWidget):
    def __init__(self, subroutine_name: str, clients: list[str]):
        super().__init__()

        self.setStyleSheet(
            """
            QFrame { background-color: #9370DB; border: 2px solid #8A2BE2; border-radius: 5px; color: white; }
            QLabel { border: none; border-radius: 0px; text-align: center; }

            """
        )

        root_layout = QVBoxLayout()

        root_frame = QFrame()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        main_layout.setSpacing(20)  # Add spacing between elements

        main_layout.addWidget(QLabel(subroutine_name))

        grid_frame = QFrame()

        grid_frame.setStyleSheet(
            """
            QFrame { background-color: none; border: none; color: white; }
            """
        )

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        grid_layout.setSpacing(20)  # Add spacing between elements

        self.sections = []

        for i, client in enumerate(clients):
            if client:
                section = Section(
                    f"{client}",
                    background_color="#7B68EE",
                    border_color="none",
                )
            else:
                section = Section(
                    "",
                    background_color="none",
                    border_color="none",
                )
                section.disappear()

            self.sections.append(section)
            grid_layout.addWidget(section, 0, i)

        grid_frame.setLayout(grid_layout)

        root_frame.setLayout(main_layout)
        root_layout.addWidget(root_frame)

        main_layout.addWidget(grid_frame)

        self.setLayout(root_layout)

    def display_result(self, results: list[str]):
        self.section.label2.setText(str(results).replace("'", ""))

    def reset(self):
        self.section.label2.setText("")

    def eventFilter(self, a0, a1):
        obj, event = a0, a1

        if event and event.type() == QEvent.MouseButtonPress:  # type: ignore
            self.on_click()
            return True
        return super().eventFilter(obj, event)

    def on_click(self):
        print("Widget clicked")


class CommentWidget(QWidget):
    def __init__(self, step_name: str):
        super().__init__()

        self.setStyleSheet(
            """
            QWidget {background-color: lightgrey; border: 2px solid grey; border-radius: 5px;}
            """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setSpacing(20)  # Add spacing between elements

        # Set label in the middle of the widget
        self.section = QLabel(step_name)
        self.section.setAlignment(Qt.AlignCenter)  # type: ignore

        layout.addWidget(self.section)

        self.setLayout(layout)

    def display_result(self, results: list[str]):
        self.section.label2.setText(str(results).replace("'", ""))

    def reset(self):
        self.section.label2.setText("")


class InputWidget(QWidget):
    def __init__(self, inputs: list[str]):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(100)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.inputs = [
            (
                Input(input)
                if input
                else Input("")
            )
            for input in inputs
        ]
        for i, input in enumerate(self.inputs):
            layout.addWidget(input, 0, i)

        self.setLayout(layout)

    def get_inputs(self):
        return [input.get_input() if input else None for input in self.inputs]

    def reset(self):
        for input in self.inputs:
            if input:
                input.input.setText("")


class StyledButton(QPushButton):
    def __init__(self, text: str, parent=None, color_scheme="blue"):
        super().__init__(text, parent)
        self.color_scheme = color_scheme
        self.setStyleSheet(self.get_button_style())
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))  # type: ignore

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

        self.setStyleSheet("""
            QListWidget::item {
                background: transparent;
                border: none;
                color: black;
            }
            QListWidget::item:selected {
                background: transparent;
                color: black;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(
        self, parties: list[str], one_step_callback, run_callback, reset_callback
    ):
        super().__init__()
        self.setWindowTitle("SMPC Visualiser")

        self.resize(1000, 800)

        self.protocol_chooser = QComboBox()

        self.client_frame = QFrame()
        client_layout = QGridLayout()
        for i, party in enumerate(parties):
            client_layout.addWidget(QLabel(party), 0, i)
        self.client_frame.setLayout(client_layout)

        self.list_widget = NoHighlightListWidget()

        self.one_step_button = StyledButton("One step", color_scheme="green")
        self.run_button = StyledButton("Run", color_scheme="blue")
        self.reset_button = StyledButton("Reset", color_scheme="red")

        layout = QVBoxLayout()
        layout.addWidget(self.protocol_chooser)
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

        self.party_indexes = {party: 0 for party in parties}

    def set_protocol_name(self, protocol_name: str):
        self.setWindowTitle(f"{protocol_name} - SMPC Visualiser")

    def update_party_names(self, parties: list[str]):
        client_layout = QGridLayout()
        for i, party in enumerate(parties):
            client_layout.addWidget(QLabel(party), 0, i)
        self.client_frame.setLayout(client_layout)

        self.num_parties = len(parties)
        self.party_indexes = {party: 0 for party in parties}

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

    def add_computation_step(self, party_name: str, calculation: str):
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

        self.party_indexes[party_name] += 1

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

        self.update_all_indexes()

        return widget

    def add_broadcast_step(self, party_name: str, variables: list[str]):
        widget = BroadcastWidget(party_name, variables)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def add_subroutine_step(self, subroutine_name: str, clients: list[str]):
        widget = SubroutineWidget(subroutine_name, clients)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint() + QSize(0, 20))
        self.list_widget.setItemWidget(list_item, widget)

        self.update_all_indexes()

        return widget

    def get_party_index(self, party_name: str):
        return list(self.party_indexes.keys()).index(party_name)

    def update_all_indexes(self):
        highest_index = max(self.party_indexes.values())
        for party in self.party_indexes:
            self.party_indexes[party] = highest_index + 1
