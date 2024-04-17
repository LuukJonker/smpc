from SMPCbox.ProtocolComputation import ProtocolComputation
from SMPCbox.ProtocolStep import ProtocolStep
from SMPCbox.ProtocolParty import ProtocolParty

if __name__ == "__main__":
    # allice = ProtocolParty("Allice", address="127.0.0.1:3829")
    # bob = ProtocolParty("Bob", address="127.0.0.1:3830")

    allice = ProtocolParty("Allice")
    bob = ProtocolParty("Bob")
    allice.set_local_variable("a", 19)
    allice.send_variable(bob, "a")
    bob.receive_variable(allice, "a")
    bob.print_local_variables()