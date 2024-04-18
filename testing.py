from SMPCbox.ProtocolComputation import ProtocolComputation
from SMPCbox.ProtocolStep import ProtocolStep
from SMPCbox.ProtocolParty import ProtocolParty
import time

if __name__ == "__main__":
    allice = ProtocolParty("Allice", address="127.0.0.1:3922")
    bob = ProtocolParty("Bob", address="127.0.0.1:3923")

    # allice = ProtocolParty("Allice")
    # bob = ProtocolParty("Bob")
    # allice.run_computation("a",  localvars['c'] + localvars['b'], "c + b")
    bob.set_local_variable("b", 218)
    bob.send_variable(allice, "b")
    allice.receive_variable(bob, "b")
    allice.set_local_variable("a", 19)
    allice.send_variable(bob, "a")
    bob.receive_variable(allice, "a")
    bob.print_local_variables()
    allice.print_local_variables()

    # closing order matters? 
    allice.exit_protocol()
    bob.exit_protocol()
