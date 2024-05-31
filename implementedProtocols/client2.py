import sys
sys.path.append('../')
from OT import OT
from SMPCbox.ProtocolParty import ProtocolParty
import time

if __name__ == "__main__":
    ot_protocol = OT()

    ot_protocol.set_party_addresses({"Sender": "127.0.0.1:4859", "Receiver": "127.0.0.1:4868"}, "Receiver")
    ot_protocol.set_input({"Receiver": {"b": 0}})
    ot_protocol()
    for step in ot_protocol.protocol_steps:
        for opp in step.step_description:
            print(opp.__str__())

    print(ot_protocol.get_output())

    ot_protocol.terminate_protocol()
