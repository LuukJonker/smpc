import sys
sys.path.append('../')
from OT import OT
from SMPCbox.ProtocolParty import ProtocolParty
import time

if __name__ == "__main__":
    ot_protocol = OT()

    ot_protocol.set_party_addresses({"Sender": "127.0.0.1:4858", "Receiver": "127.0.0.1:4868"}, "Receiver")
    ot_protocol.set_input({"Receiver": {"b": 1}})
    ot_protocol()

    print(ot_protocol.get_output())

    ot_protocol.terminate_protocol()
