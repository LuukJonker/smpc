from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

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
