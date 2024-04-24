# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')
import time
from SMPCbox import AbstractProtocol
from SMPCbox.ProtocolParty import ProtocolParty
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import os


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


class OT(AbstractProtocol):
    def __init__(self):
        super().__init__()

    def get_expected_input(self) -> dict[str, list[str]]:
        return {"Sender":["m0","m1"],"Receiver":["b"]}
    
    def get_party_roles(self) -> list[str]:
        return ["Sender", "Receiver"]
    
    def output_variables(self) -> dict[str, list[str]]:
        return {"Receiver": ["mb"]}
    
    def __call__(self):
        sender = self.parties["Sender"]
        receiver = self.parties["Receiver"]

        self.add_protocol_step("OT step")

        self.compute(sender, ["N", "d", "e"], [], getRSAvars, "RSA()")
        self.send_variables(sender, receiver, ["N", "e"])
        self.compute(sender, ["x0", "x1"], [], lambda: (int.from_bytes(os.urandom(16), byteorder='big'), int.from_bytes(os.urandom(16), byteorder='big')), "rand()")
        self.send_variables(sender, receiver, ["x0", "x1"])

        # Calculate v
        self.compute(receiver, "k", [], lambda: (int.from_bytes(os.urandom(16), byteorder='big')), "rand()")
        self.compute(receiver, "x_b", ["b", "x0", "x1"], lambda b, x0, x1: x0 if (b == 0) else x1, "choose x_b")
        self.compute(receiver, "v", ["x_b", "k", "e", "N"], lambda xb, k, e, N: ((xb + pow(k, e)) % N), "(x_b + k^e) mod N")
        self.send_variables(receiver, sender, "v")

        # calculate the encrypted m0 and m1
        self.compute(sender, "k0", ["v", "x0", "d", "N"], lambda v, x, d, N: pow(v-x, d, N), "(v-x0)^d mod N")
        self.compute(sender, "k1", ["v", "x1", "d", "N"], lambda v, x, d, N: pow(v-x, d, N), "(v-x1)^d mod N")
        self.compute(sender, "m0_enc", ["m0", "k0", "N"], lambda m, k, N: ((m+k) % N), "(m0 + k0) mod N")
        self.compute(sender, "m1_enc", ["m1", "k1", "N"], lambda m, k, N: ((m+k) % N), "(m1 + k1) mod N")
        self.send_variables(sender, receiver, ["m0_enc", "m1_enc"])

        self.compute(receiver, "mb_enc", ["b", "m0_enc", "m1_enc"], lambda b, m0, m1: (m0 if (b == 0) else m1), "choose m_b")
        self.compute(receiver, "mb", ["mb_enc", "k", "N"], lambda mb, k, N: ((mb - k) % N), "(m'_b - k) mod N")

        



if __name__ == "__main__":
    ot_protocol = OT()

    sender = ProtocolParty("Alice", address="127.0.0.1:4841")
    receiver = ProtocolParty("Bob", address="127.0.0.1:4840", is_listening_socket=False)
    time.sleep(5)
    ot_protocol.set_protocol_parties({"Sender": sender, "Receiver": receiver})
    ot_protocol.set_running_party("Sender", sender)
    ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}})
    # ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}, "Receiver": {"b": 1}})
    ot_protocol()

    for step in ot_protocol.protocol_steps:
        for opp in step.step_description:
            print(opp.__str__())
    
    print(ot_protocol.get_output())
    ot_protocol.terminate_protocol()
