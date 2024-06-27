from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import QEvent
from .section import Section

class SubroutineWidget(QWidget):
    def __init__(self, subroutine_name: str, clients: list[str], subroutine_object: object):
        super().__init__()

        self.setStyleSheet(
            """
            QFrame { background-color: #9370DB; border: 2px solid #8A2BE2; border-radius: 5px; color: white; }
            QLabel { border: none; border-radius: 0px; text-align: center; }

            """
        )

        self.subroutine_object = subroutine_object

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

        self.sections: list[Section] = []

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

    def display_result(self, results: dict[str, dict[str, str]]):
        for section in self.sections:
            if section.text in results:
                section.add_computation(str(results[section.text]))

    def reset(self):
        self.section.label2.setText("")

    def on_click(self):
        self.subroutine_object.show() # type: ignore
