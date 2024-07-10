from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame
from .section import Section
from SMPCbox.ProtocolParty import TrackedStatistics


def format_statistics(statistics: TrackedStatistics, name: str) -> str:
    return f"""
    {name} Statistics

    execution_time: {statistics.execution_time}
    execution_CPU_time: {statistics.execution_CPU_time}
    wait_time: {statistics.wait_time}
    messages_send: {statistics.messages_send}
    bytes_send: {statistics.bytes_send}
    messages_received: {statistics.messages_received}
    bytes_received: {statistics.bytes_received}"""


class StatisticsWidget(QWidget):
    def __init__(
        self,
        party_statistics: dict[str, TrackedStatistics],
        protocol_statistics: TrackedStatistics,
    ):
        super().__init__()

        main_layout = QVBoxLayout()

        section_frame = QFrame()

        section_layout = QGridLayout()
        section_layout.setContentsMargins(
            10, 10, 10, 10
        )  # Add margins around the widget
        section_layout.setHorizontalSpacing(
            30
        )  # Add horizontal spacing between columns

        self.sections = [
            Section(
                format_statistics(statistic, name),
                background_color="#FF6347",
                border_color="#FF4500",
            )
            for name, statistic in party_statistics.items()
        ]
        for i, column in enumerate(self.sections):
            section_layout.addWidget(column, 0, i)

        section_frame.setLayout(section_layout)
        main_layout.addWidget(section_frame)

        # overall_section = Section(
        #     format_statistics(protocol_statistics, "Overall"),
        #     background_color="#FF6347",
        #     border_color="#FF4500",
        # )

        # main_layout.addWidget(overall_section)

        self.setLayout(main_layout)
