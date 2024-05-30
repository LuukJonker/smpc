import sys
sys.path.append('../')


from implementedProtocols import OT, SecretShareMultiplication
from SMPCbox import TrackedStatistics, AbstractProtocol
from typing import Any, Type
from statistics import mean, stdev
import time

class TestResult:
    # each stat contains the (average, standard deviation)
    def __init__(self):
        # Stats reported by SMPCbox
        self.reported_execution_time: tuple[float, float] = (0,0)
        self.reported_wait_time: tuple[float, float] = (0,0)
        self.reported_energy_consumption: tuple[float, float] = (0,0)

        # Total measured for the call to the protocol
        self.total_execution_time: tuple[float, float] = (0,0)
        self.total_energy_consumption: tuple[float, float] = (0,0)

    
    def __str__(self):
        return f"""
        Result

        SMPCbox stats:
            execution_time: {self.reported_execution_time}
            wait_time: {self.reported_wait_time}
            energy_consumption: {self.reported_energy_consumption}
        
        Measured stats for protocol call:
            execution_time: {self.total_execution_time}
            energy_consumption: {self.total_energy_consumption}"""
    


def run_protocol_simulated(protocol_class: Type[AbstractProtocol], protocol_input: dict[str, dict[str, Any]], num_repeats=10, init_args=()) -> TestResult:
    smpcbox_statistics: list[TrackedStatistics] = []
    measured_times = []
    for _ in range(num_repeats):
        protocol = protocol_class(*init_args)
        protocol.set_input(protocol_input)
        s = time.time()
        protocol()
        e = time.time()
        measured_times.append(e - s)
        smpcbox_statistics.append(protocol.get_total_statistics())
    
    test_result = TestResult()
    reported_execution_times = [stats.execution_time for stats in smpcbox_statistics]
    reported_wait_times = [stats.wait_time for stats in smpcbox_statistics]
    
    test_result.reported_execution_time = (mean(reported_execution_times), stdev(reported_execution_times))
    test_result.reported_wait_time = (mean(reported_wait_times), stdev(reported_wait_times))

    test_result.total_execution_time = (mean(measured_times), stdev(measured_times))
    return test_result

print(run_protocol_simulated(OT, {"Sender": {"m0": 10, "m1": 11}, "Receiver": {"b": 0}}))


print(run_protocol_simulated(SecretShareMultiplication, {"Alice": {"a": 10}, "Bob": {"b": 48}}))

