# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')

import time
import os
from SMPCbox import AbstractProtocol, ProtocolParty
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa


def getRSAvars():
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    d = private_key.private_numbers().d
    public_key = private_key.public_key()

    # Extracting e and N from the public key
    e = public_key.public_numbers().e
    N = public_key.public_numbers().n
    return N, d, e

def rand():
    return int.from_bytes(os.urandom(16), byteorder='big')

class OT(AbstractProtocol):
    protocol_name="ObliviousTransfer"

    def __init__(self):
        super().__init__()

    def get_expected_input(self) -> dict[str, list[str]]:
        return {"Sender":["m0","m1"],"Receiver":["b"]}
    
    def get_party_names(self) -> list[str]:
        return ["Sender", "Receiver"]
    
    def output_variables(self) -> dict[str, list[str]]:
        return {"Receiver": ["mb"]}
    
    def Sender(self):
        sender = self.parties["Sender"]
        receiver = self.parties["Receiver"]

        self.compute(sender, ["N", "d", "e"], getRSAvars(), "RSA()")
        self.send_variables(sender, receiver, ["N", "e"])
        self.send_variables(sender, receiver, ["N", "e"])
        self.compute(sender, ["x0", "x1"], (rand(), rand()), "rand()")
        self.send_variables(sender, receiver, ["x0", "x1"])

        # receiver computes v

        self.receive_variables(receiver, sender, "v")
        self.compute(sender, "k0", pow(sender["v"]-sender["x0"], sender["d"], sender["N"]), "(v-x0)^d mod N")
        self.compute(sender, "k1", pow(sender["v"]-sender["x1"], sender["d"], sender["N"]), "(v-x1)^d mod N")
        self.compute(sender, "m0_enc", (sender["m0"]+sender["k0"]) % sender["N"], "(m0 + k0) mod N")
        self.compute(sender, "m1_enc", (sender["m1"]+sender["k1"]) % sender["N"], "(m1 + k1) mod N")
        self.send_variables(sender, receiver, ["m0_enc", "m1_enc"])

    def Receiver(self):
        sender = self.parties["Sender"]
        receiver = self.parties["Receiver"]

        self.receive_variables(sender, receiver, ["N", "d", "e", "x0", "x1"])
        self.compute(receiver, "k", rand(), "rand()")
        self.compute(receiver, "x_b", receiver["x0"] if (receiver["b"] == 0) else receiver["x1"], "choose x_b")
        self.compute(receiver, "v", (receiver["x_b"] + pow(receiver["k"], receiver["e"])) % receiver["N"], "(x_b + k^e) mod N")
        self.send_variables(receiver, sender, "v")

        # sender calculates m0_enc, m1_enc

        self.receive_variables(sender, receiver, ["m0_enc", "m1_enc"])
        self.compute(receiver, "mb_enc", receiver["m0_enc"] if (receiver["b"] == 0) else receiver["m1_enc"], "choose m_b")
        self.compute(receiver, "mb", (receiver["mb_enc"] - receiver["k"]) % receiver["N"], "(m'_b - k) mod N")

    def execute_party(self, party_name: str):
        self.add_protocol_step("Step")
        self.run_party_method(party_name)

if __name__ == "__main__":
    ot_protocol = OT()

    ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}, "Receiver": {"b": 1}})
    s = time.time()
    ot_protocol()
    e = time.time()
    print("OT time", e-s)
    for role, stats in ot_protocol.get_statistics().items():
        print(role)
        print(stats)

    # sender = ProtocolParty("Alice", address="127.0.0.1:4841")
    # receiver = ProtocolParty("Bob", address="127.0.0.1:4840", is_listening_socket=False)
    # time.sleep(5)
    # ot_protocol.set_protocol_parties({"Sender": sender, "Receiver": receiver})
    # ot_protocol.set_running_party("Sender", sender)
    # ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}})
    # # ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}, "Receiver": {"b": 1}})
    # ot_protocol()

    # for step in ot_protocol.protocol_steps:
    #     for opp in step.step_description:
    #         print(opp.__str__())
    
    # print(ot_protocol.get_output())
    # ot_protocol.terminate_protocol()
