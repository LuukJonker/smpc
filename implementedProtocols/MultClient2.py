import sys
sys.path.append('../')
from MultiplicationProtocol import SecretShareMultiplication
from SMPCbox.ProtocolParty import ProtocolParty
import time


if __name__ == "__main__":
    alice =ProtocolParty("Alice", "127.0.0.1:3299", is_listening_socket=False)
    bob = ProtocolParty("Bob", "127.0.0.1:3300")
    time.sleep(5)
    p = SecretShareMultiplication(l=32)
    p.set_protocol_parties({"Alice": alice, "Bob": bob})
    p.set_running_party("Bob", bob)
    p.set_input({"Bob": {"b": 13}})

    p()

    print(p.get_output())

    p.terminate_protocol()