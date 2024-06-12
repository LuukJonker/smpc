import sys
sys.path.append('../')


from implementedProtocols import OT, SecretShareMultiplication, Sum
from SMPCbox import TrackedStatistics, AbstractProtocol
from typing import Any, Type
from statistics import mean, stdev
import multiprocessing as mp
import pandas as pd
import time

class TestResult:
    # each stat contains the (average, standard deviation)
    def __init__(self):
        # Stats reported by SMPCbox
        self.reported_execution_time: tuple[float, float] = (0,0)
        self.reported_CPU_time: tuple[float, float] = (0,0)
        self.reported_wait_time: tuple[float, float] = (0,0)
        self.reported_energy_consumption: tuple[float, float] = (0,0)

        # Total measured for the call to the protocol
        self.total_execution_time: tuple[float, float] = (0,0)
        self.total_CPU_time: tuple[float, float] = (0,0)
        self.total_energy_consumption: tuple[float, float] = (0,0)

    
    def __str__(self):
        return f"""
        Result

        SMPCbox stats:
            execution_time: {self.reported_execution_time}
            CPU_time: {self.reported_CPU_time}
            wait_time: {self.reported_wait_time}
            energy_consumption: {self.reported_energy_consumption}
        
        Measured stats for protocol call:
            execution_time: {self.total_execution_time}
            CPU_time: {self.total_CPU_time}
            energy_consumption: {self.total_energy_consumption}"""


def run_protocol_simulated(protocol_class: Type[AbstractProtocol], protocol_input: dict[str, dict[str, Any]], num_repeats=10, init_args=()) -> TestResult:
    smpcbox_statistics: list[TrackedStatistics] = []
    measured_times = []
    measured_CPU_times = []
    for _ in range(num_repeats):
        protocol = protocol_class(*init_args)
        protocol.set_input(protocol_input)
        s = time.perf_counter()
        s_CPU = time.process_time()
        protocol()
        e_CPU = time.process_time()
        e = time.perf_counter()
        measured_times.append(e - s)
        measured_CPU_times.append(e_CPU - s_CPU)
        smpcbox_statistics.append(protocol.get_total_statistics())
    
    test_result = TestResult()
    reported_execution_times = [stats.execution_time for stats in smpcbox_statistics]
    reported_CPU_times = [stats.execution_CPU_time for stats in smpcbox_statistics]
    reported_wait_times = [stats.wait_time for stats in smpcbox_statistics]
    
    test_result.reported_execution_time = (mean(reported_execution_times), stdev(reported_execution_times))
    test_result.reported_wait_time = (mean(reported_wait_times), stdev(reported_wait_times))
    test_result.reported_CPU_time = (mean(reported_CPU_times), stdev(reported_CPU_times))

    test_result.total_CPU_time = (mean(measured_CPU_times), stdev(measured_CPU_times))
    test_result.total_execution_time = (mean(measured_times), stdev(measured_times))
    return test_result



def run_party(protocol_class: Type[AbstractProtocol], addrs: dict[str, str], protocol_input: dict[str, dict[str, Any]], init_args=()):
    pass


def get_addresses(start_port, parties):
    addresses = {}
    for i, party in enumerate(parties):
        addresses[party] = f"127.0.0.1:{start_port+i}"
    return addresses

def run_protocol_distributed(protocol_class: Type[AbstractProtocol], protocol_input: dict[str, dict[str, Any]], num_repeats=10, init_args=()) -> TestResult:
    p = protocol_class(*init_args)
    parties = p.get_party_names()

    start_port = 10000
    for _ in range(num_repeats):
        addrs = get_addresses(start_port, parties)
        start_port += len(parties)
        
    



def get_result_dict() ->  dict[str, list[float]]:
    d = {}
    d["reported_execution_time_avg"] = []
    d["reported_execution_time_std"] = []
    d["reported_CPU_time_avg"] = []
    d["reported_CPU_time_std"] = []
    d["reported_wait_time_avg"] = []
    d["reported_wait_time_std"] = []
    d["reported_energy_consumption_avg"] = []
    d["reported_energy_consumption_std"] = []
    d["total_execution_time_avg"] = []
    d["total_execution_time_std"] = []
    d["total_CPU_time_avg"] = []
    d["total_CPU_time_std"] = []
    d["total_energy_consumption_avg"] = []
    d["total_energy_consumption_std"] = []
    return d

def add_result(d: dict[str, list[float]], new_res: TestResult):
    d["reported_execution_time_avg"].append(new_res.reported_execution_time[0])
    d["reported_execution_time_std"].append(new_res.reported_execution_time[1])
    d["reported_CPU_time_avg"].append(new_res.reported_CPU_time[0])
    d["reported_CPU_time_std"].append(new_res.reported_CPU_time[1])
    d["reported_wait_time_avg"].append(new_res.reported_wait_time[0])
    d["reported_wait_time_std"].append(new_res.reported_wait_time[1])
    d["reported_energy_consumption_avg"].append(new_res.reported_energy_consumption[0])
    d["reported_energy_consumption_std"].append(new_res.reported_energy_consumption[1])
    d["total_execution_time_avg"].append(new_res.total_execution_time[0])
    d["total_execution_time_std"].append(new_res.total_execution_time[1])
    d["total_CPU_time_avg"].append(new_res.total_CPU_time[0])
    d["total_CPU_time_std"].append(new_res.total_CPU_time[1])
    d["total_energy_consumption_avg"].append(new_res.total_energy_consumption[0])
    d["total_energy_consumption_std"].append(new_res.total_energy_consumption[1])

def run_sum_test(min_parties, max_parties):
    results = get_result_dict()
    results["num_parties"] = []

    for n in range(min_parties, max_parties + 1):
        input = {}
        for i in range(n):
            input[f"party_{i}"] = {"value" : 2}
        
        print(f"Parties {n}")
        result = run_protocol_simulated(Sum.Sum, input, init_args=[n], num_repeats=50)
        add_result(results, result)
        results["num_parties"].append(n)
    
    pd.DataFrame(results).to_csv("sumTest.csv")
        


# run_sum_test(2, 500)

# print(run_protocol_simulated(OT, {"Sender": {"m0": 1, "m1": 2}, "Receiver": {"b": 0}}))
# print(run_protocol_simulated(SecretShareMultiplication, {"Alice": {"a": 4}, "Bob": {"b": 3}}))

