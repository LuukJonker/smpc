from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .section import Section

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
