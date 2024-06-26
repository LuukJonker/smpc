from typing import Any
import math
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QGridLayout, QWidget
from PyQt5.QtCore import QPoint
from .section import Section

class SendReceiveWidget(QWidget):
    def __init__(
        self,
        num_columns: int,
        sender: int,
        receiver: int,
        variables: dict[str, Any],
    ):
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the widget
        layout.setHorizontalSpacing(100)  # Add horizontal spacing between columns
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows

        for i in range(num_columns):
            if i != sender and i != receiver:
                section = Section("", background_color="none", border_color="none")
                section.disappear()
                layout.addWidget(section, 0, i)

        variables_string = str(variables).replace("'", "").replace(", ", "\n")[1:-1]

        self.send_section = Section(
            f"""Send\n\n{variables_string}""",
            background_color="lightgreen",
            border_color="green",
        )
        self.receive_section = Section(
            f"""Receive\n\n{variables_string}""",
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
