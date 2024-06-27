from PyQt5.QtWidgets import QWidget, QGridLayout
from .section import Section

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

    def update_result(self, index: int, result: str):
        self.sections[index].label2.setText(result)
