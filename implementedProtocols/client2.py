import sys
sys.path.append('../')
from OT import OT
from SMPCbox.ProtocolParty import ProtocolParty
import time

if __name__ == "__main__":
    ot_protocol = OT()

    sender = ProtocolParty("Bas", address="127.0.0.1:4832", is_listening_socket=False)
    receiver = ProtocolParty("Naz-Pari", address="127.0.0.1:4833")
    time.sleep(5)
    ot_protocol.set_protocol_parties({"Sender": sender, "Receiver": receiver})
    ot_protocol.set_running_party("Receiver", receiver)
    ot_protocol.set_input({"Receiver": {"b": 0}})
    ot_protocol()
    for step in ot_protocol.protocol_steps:
        for opp in step.step_description:
            print(opp.__str__())
