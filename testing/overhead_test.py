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
    
def compile_test_result(stats: list[TrackedStatistics], measured_times: list[float], measured_CPU_times: list[float]) -> TestResult:
    test_result = TestResult()
    reported_execution_times = [stats.execution_time for stats in stats]
    reported_CPU_times = [stats.execution_CPU_time for stats in stats]
    reported_wait_times = [stats.wait_time for stats in stats]
    
    test_result.reported_execution_time = (mean(reported_execution_times), stdev(reported_execution_times))
    test_result.reported_wait_time = (mean(reported_wait_times), stdev(reported_wait_times))
    test_result.reported_CPU_time = (mean(reported_CPU_times), stdev(reported_CPU_times))

    test_result.total_CPU_time = (mean(measured_CPU_times), stdev(measured_CPU_times))
    test_result.total_execution_time = (mean(measured_times), stdev(measured_times))
    return test_result

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
    
    
    return compile_test_result(smpcbox_statistics, measured_times, measured_CPU_times)

class DistributedTestStats():
    def __init__(self):
        self.stats: TrackedStatistics = TrackedStatistics()
        self.total_cpu_time: float = 0.0
        self.total_exec_time: float = 0.0
    
    def __add__(self, other):
        res = DistributedTestStats()
        res.stats = self.stats + other.stats
        res.total_cpu_time = self.total_cpu_time + other.total_cpu_time
        res.total_exec_time = self.total_exec_time + other.total_exec_time
        return res

def run_party(protocol_class: Type[AbstractProtocol], addrs: dict[str, str], local_p: str, protocol_input: dict[str, dict[str, Any]], queue, init_args=()):
    try:
        p = protocol_class(*init_args)
        p.set_input(protocol_input)
        p.set_party_addresses(addrs, local_p)
    except Exception as e:
        print(e)
        queue.put("EXCEPTION")
        return
    
    s = time.perf_counter()
    s_CPU = time.process_time()
    p()
    e_CPU = time.process_time()
    e = time.perf_counter()
    p.terminate_protocol()
    res = DistributedTestStats()
    res.stats = p.get_total_statistics()
    res.total_cpu_time = e_CPU - s_CPU
    res.total_exec_time = e - s
    queue.put(res)   

def get_addresses(start_port, parties):
    addresses = {}
    for i, party in enumerate(parties):
        addresses[party] = f"127.0.0.1:{start_port+i}"
    return addresses

def run_distributed_once(start_port, parties, protocol_class, protocol_input, init_args):
    q = mp.Queue()
    addrs = get_addresses(start_port, parties)
    processes: list[mp.Process] = []
    for party in parties:
        processes.append(mp.Process(target=run_party, args=(protocol_class, addrs, party, protocol_input, q, init_args)))
    
    [p.start() for p in processes]
    [p.join() for p in processes]

    res = DistributedTestStats()

    while not q.empty():
        if res == "EXCEPTION":
            print("EXCEPTION")
            time.sleep(120)
            print("STARTING again")
            run_distributed_once(9000, parties, protocol_class, protocol_input, init_args)
        res += q.get()
    return res

def run_protocol_distributed(protocol_class: Type[AbstractProtocol], protocol_input: dict[str, dict[str, Any]], num_repeats=10, init_args=(), start_port=10000) -> TestResult:
    protocol = protocol_class(*init_args)
    parties = protocol.get_party_names()

    results: list[DistributedTestStats] = []

    for _ in range(num_repeats):
        res = run_distributed_once(start_port, parties, protocol_class, protocol_input, init_args)
        results.append(res)

        # off set the ports to prevent reuse of ports that are timed out
        start_port += len(parties)

    smpcbox_stats = [res.stats for res in results]
    measured_times = [res.total_exec_time for res in results]
    measured_CPU_times = [res.total_cpu_time for res in results]
    return compile_test_result(smpcbox_stats, measured_times, measured_CPU_times)


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

def run_simulated_sum_test(min_parties, max_parties):
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
    
    pd.DataFrame(results).to_csv("simulatedSumTest.csv")
        
def run_distributed_sum_test(min_parties, max_parties):
    results = get_result_dict()
    results["num_parties"] = []
    cur_port = 12000

    for n in range(min_parties, max_parties + 1):
        input = {}
        for i in range(n):
            input[f"party_{i}"] = {"value" : 2}
        
        print(f"Parties {n}, cur_port: {cur_port}")
        result = run_protocol_distributed(Sum.Sum, input, init_args=[n], num_repeats=50, start_port=cur_port)
        add_result(results, result)
        results["num_parties"].append(n)
        cur_port += n*50
        if cur_port > 20000:
            cur_port = 12000
    
    pd.DataFrame(results).to_csv("distributedSumTest.csv")

run_distributed_sum_test(2, 50)
# run_simulated_sum_test(2, 500)
# print(run_protocol_distributed(OT, {"Sender": {"m0": 1, "m1": 2}, "Receiver": {"b": 0}}))

# print(run_protocol_simulated(OT, {"Sender": {"m0": 1, "m1": 2}, "Receiver": {"b": 0}}))
# print(run_protocol_simulated(SecretShareMultiplication, {"Alice": {"a": 4}, "Bob": {"b": 3}}))

