from PyQt5.QtWidgets import QWidget, QGridLayout
from .section import Section
from SMPCbox.ProtocolParty import TrackedStatistics

class StatisticsWidget(QWidget):
    def __init__(self, party_statistics: dict[str, TrackedStatistics], protocol_statistics: TrackedStatistics):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(50)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        self.sections = [Section(str(statistic), background_color="#FF6347", border_color="#FF4500") for statistic in party_statistics.values()]
        for i, column in enumerate(self.sections):
            layout.addWidget(column, 0, i)

            if column.label1.text() == "":
                column.disappear()

        self.setLayout(layout)

