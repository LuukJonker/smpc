from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt


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
        self.label1 = QLabel(str(text))
        self.label1.setWordWrap(True)
        self.label1.setAlignment(Qt.AlignCenter)  # type: ignore
        self.label2 = QLabel("")
        self.label2.setWordWrap(True)
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
