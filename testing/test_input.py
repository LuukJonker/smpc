import sys
sys.path.append('../')


import multiprocessing as mp
from SMPCbox.AbstractProtocol import AbstractProtocol
from typing import Type, Any

def run_party(protocol_class: Type[AbstractProtocol], addrs: dict[str, str], local_p: str, protocol_input: dict[str, dict[str, Any]], queue, init_args=(), extra_return_vars={}):
    try:
        p = protocol_class(*init_args)
        p.set_input(protocol_input)
        p.set_party_addresses(addrs, local_p)
    except Exception as e:
        print(e)
        queue.put("EXCEPTION")
        return
    p()

    extra_vars = {}
    if local_p in extra_return_vars:
        for var in extra_return_vars[local_p]:
            extra_vars[var] = p.parties[local_p][var]
    out = p.get_output()
    if local_p in out:
        out[local_p].update(extra_vars)
    else:
        out[local_p] = extra_vars

    queue.put(out)
    p.terminate_protocol()

def get_addresses(start_port, parties):
    addresses = {}
    for i, party in enumerate(parties):
        addresses[party] = f"127.0.0.1:{start_port+i}"
    return addresses


def test_distributed(protocol_class: Type[AbstractProtocol], input, start_port, init_args=(), extra_return_vars={}):
    q = mp.Queue()
    processes: list[mp.Process] = []
    protocol = protocol_class(*init_args)
    addrs = get_addresses(start_port, protocol.party_names())
    for party in protocol.party_names():
        processes.append(mp.Process(target=run_party, args=(protocol_class, addrs, party, input, q, init_args, extra_return_vars)))
    
    [p.start() for p in processes]
    [p.join() for p in processes]

    outputs = {}
    while not q.empty():
        outputs.update(q.get())

    return outputs

def add_extra_vars_to_output(output, protocol: AbstractProtocol, extra_return_vars):
    for party, vars in extra_return_vars.items():
        if party not in output:
            output[party] = {}
        for var in vars:
            val = protocol.parties[party][var]
            output[party][var] = val
    return output


def test_simulated(protocol_class: Type[AbstractProtocol], input, init_args=(), extra_return_vars={}):
    p = protocol_class(*init_args)
    p.set_input(input)
    p()
    out = p.get_output()
    return add_extra_vars_to_output(out, p, extra_return_vars)
