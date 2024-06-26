from enum import Enum
from multiprocessing import Queue
from typing import Any


class Step(Enum):
    COMMENT = 1
    COMPUTATION = 2
    SEND = 3
    BROADCAST = 4
    SUBROUTINE = 5
    END_SUBROUTINE = 6
    END_PROTOCOL = 7


class ProtocolSide:
    def __init__(self, queue: Queue):
        self.queue = queue

    def add_comment(self, comment: str):
        self.queue.put((Step.COMMENT, (comment,)))

    def add_computation(
        self,
        party_name: str,
        computed_vars: dict[str, Any],
        computation: str,
    ):
        self.queue.put((Step.COMPUTATION, (party_name, computed_vars, computation)))

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        self.queue.put(
            (Step.SEND, (sending_party_name, receiving_party_name, variables))
        )

    def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
        self.queue.put((Step.BROADCAST, (party_name, variables)))

    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        self.queue.put(
            (
                Step.SUBROUTINE,
                (subroutine_name, party_mapping, input_mapping, output_mapping),
            )
        )

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        self.queue.put((Step.END_SUBROUTINE, (output_values,)))

    def end_protocol(self):
        self.queue.put((Step.END_PROTOCOL, ()))