from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)
from typing import Any


class Input(QWidget):
    def __init__(self, prompt: str, background_color="lightgrey", border_color="grey"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{background-color: {background_color}; border: 2px solid {border_color}; border-radius: 5px;}}
            QLabel {{border: none; border-radius: 0px; text-align: center;}}
            """
        )

        self.background_color = background_color
        self.border_color = border_color

        if prompt == "":
            self.setStyleSheet(
                "opacity: 0; color: white; border: none; background-color: none;"
            )

        layout = QHBoxLayout()

        self.prompt = prompt

        self.frame = QFrame()
        self.prompt_label = QLabel(f"{prompt}: ")
        self.input = QLineEdit()
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")  # Style for error message
        self.error_label.hide()  # Hide error label initially

        layout.addWidget(self.prompt_label)
        layout.addWidget(self.input)
        self.frame.setLayout(layout)

        frame_layout = QVBoxLayout()
        frame_layout.addWidget(self.frame)
        frame_layout.addWidget(self.error_label)  # Add the error label to the layout
        self.setLayout(frame_layout)

    def get_input(self):
        return self.input.text()

    def set_input(self, value: str):
        self.input.setText(value)

    def on_change(self, callback):
        self.input.textChanged.connect(callback)

    def set_immutable(self):
        self.input.setReadOnly(True)

    def display_error(self, error: str):
        if error:
            self.error_label.setText(error)
            self.error_label.show()
            self.setStyleSheet(
                """
                QFrame {background-color: #FF6347; border: 2px solid #FF4500; border-radius: 5px;}
                QLabel {border: none; border-radius: 0px; text-align: center;}
                """
            )
        else:
            self.error_label.hide()
            self.setStyleSheet(
                f"""
                QFrame {{background-color: {self.background_color}; border: 2px solid {self.border_color}; border-radius: 5px;}}
                QLabel {{border: none; border-radius: 0px; text-align: center;}}
                """
            )


class InputWidget(QWidget):
    def __init__(self, inputs: list[str], defaults: list[Any] | None, mutable: bool = True):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(100)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.inputs = [(Input(input) if input else Input("")) for input in inputs]
        for i, input in enumerate(self.inputs):
            if not mutable:
                input.set_immutable()

            if defaults and defaults[i] is not None:
                input.set_input(str(defaults[i]))

            layout.addWidget(input, 0, i)

        self.setLayout(layout)

    def get_inputs(self):
        return [
            (widget.prompt, widget.get_input()) if widget.prompt else None
            for widget in self.inputs
        ]

    def reset(self):
        for widget in self.inputs:
            if widget:
                widget.input.setText("")
