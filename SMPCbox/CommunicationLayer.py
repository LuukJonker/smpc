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
        """Add a comment to the visualizer.

        Args:
            comment (str): The comment.
        """
        self.queue.put((Step.COMMENT, (comment,)))

    def add_computation(
        self,
        party_name: str,
        computed_vars: dict[str, Any],
        computation: str,
    ):
        """Add a computation to the visualizer.

        Args:
            party_name (str): The name of the party that performed the computation.
            computed_vars (dict[str, Any]): The variables that were computed with their values.
            computation (str): The computation that was performed.
        """
        self.queue.put((Step.COMPUTATION, (party_name, computed_vars, computation)))

    def send_message(
        self,
        sending_party_name: str,
        receiving_party_name: str,
        variables: dict[str, Any],
    ):
        """Send a message from one party to another.

        Args:
            sending_party_name (str): The name of the party sending the message.
            receiving_party_name (str): The name of the party receiving the message.
            variables (dict[str, Any]): The variables that are being sent with their values.
        """

        self.queue.put(
            (Step.SEND, (sending_party_name, receiving_party_name, variables))
        )

    def broadcast_variable(self, party_name: str, variables: dict[str, Any]):
        """Broadcast a variable to all parties.

        Args:
            party_name (str): The name of the party broadcasting the variable.
            variables (dict[str, Any]): The variables that are being broadcasted with their values.
        """

        self.queue.put((Step.BROADCAST, (party_name, variables)))

    def start_subroutine(
        self,
        subroutine_name: str,
        party_mapping: dict[str, str],
        input_mapping: dict[str, dict[str, str]],
        output_mapping: dict[str, dict[str, str]],
    ):
        """Start a subroutine.

        Args:
            subroutine_name (str): The name of the subroutine.
            party_mapping (dict[str, str]): The mapping from party names to their roles.
            input_mapping (dict[str, dict[str, str]]): The mapping from party names to input variables.
            output_mapping (dict[str, dict[str, str]]): The mapping from party names to output variables.
        """

        self.queue.put(
            (
                Step.SUBROUTINE,
                (subroutine_name, party_mapping, input_mapping, output_mapping),
            )
        )

    def end_subroutine(self, output_values: dict[str, dict[str, Any]]):
        """End a subroutine.

        Args:
            output_values (dict[str, dict[str, Any]]): The output values of the subroutine.
        """

        self.queue.put((Step.END_SUBROUTINE, (output_values,)))

    def end_protocol(self, party_statistics: dict[str, Any], protocol_statistics: Any):
        """End the protocol.

        Args:
            party_statistics (dict[str, Any]): The statistics of each party.
            protocol_statistics (Any): The statistics of the protocol.
        """

        self.queue.put((Step.END_PROTOCOL, (party_statistics, protocol_statistics)))
