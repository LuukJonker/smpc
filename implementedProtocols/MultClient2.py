from MultiplicationProtocol import SecretShareMultiplication
from SMPCbox.ProtocolParty import ProtocolParty
import time


if __name__ == "__main__":
    p = SecretShareMultiplication(l=32)
    p.set_party_addresses({"Bob": "127.0.0.1:4859", "Alice": "127.0.0.1:4869"}, "Bob")
    p.set_input({"Bob": {"b": 13}})

    p()

    print(p.get_output())

    p.terminate_protocol()