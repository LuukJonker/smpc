# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')

from SMPCbox import AbstractProtocol

import time
from SMPCbox import AbstractProtocol, ProtocolParty
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
    protocol_name="ObliviousTransfer"

    def __init__(self):
        super().__init__()

    def input_variables(self) -> dict[str, list[str]]:
        return {"Sender":["m0","m1"],"Receiver":["b"]}
    
    def party_names(self) -> list[str]:
        return ["Sender", "Receiver"]
    
    def output_variables(self) -> dict[str, list[str]]:
        return {"Receiver": ["mb"]}
    
    def __call__(self):
        p_send = self.parties["Sender"]
        p_recv = self.parties["Receiver"]

        self.compute(p_send, ["N", "d", "e"], getRSAvars, "RSA()")
        self.send_variables(p_send, p_recv, ["N", "e"])
        self.compute(p_send, ["x0", "x1"], lambda: (int.from_bytes(os.urandom(16), byteorder='big'), int.from_bytes(os.urandom(16), byteorder='big')), "rand()")
        self.send_variables(p_send, p_recv, ["x0", "x1"])

        # Calculate v
        self.compute(p_recv, "k", lambda: (int.from_bytes(os.urandom(16), byteorder='big')), "rand()")
        self.compute(p_recv, "x_b", lambda: p_recv["x0"] if (p_recv["b"] == 0) else p_recv["x1"], "choose x_b")
        self.compute(p_recv, "v", lambda: ((p_recv["x_b"] + pow(p_recv["k"], p_recv["e"])) % p_recv["N"]), "(x_b + k^e) mod N")
        self.send_variables(p_recv, p_send, "v")

        # calculate the encrypted m0 and m1
        self.compute(p_send, "k0", lambda: pow(p_send["v"] - p_send["x0"], p_send["d"], p_send["N"]), "(v-x0)^d mod N")
        self.compute(p_send, "k1", lambda: pow(p_send["v"] - p_send["x1"], p_send["d"], p_send["N"]), "(v-x1)^d mod N")
        self.compute(p_send, "m0_enc", lambda: ((p_send["m0"] + p_send["k0"]) % p_send["N"]), "(m0 + k0) mod N")
        self.compute(p_send, "m1_enc", lambda: ((p_send["m1"] + p_send["k1"]) % p_send["N"]), "(m1 + k1) mod N")
        self.send_variables(p_send, p_recv, ["m0_enc", "m1_enc"])

        self.compute(p_recv, "mb_enc", lambda: (p_recv["m0_enc"] if (p_recv["b"] == 0) else p_recv["m1_enc"]), "choose m_b")
        self.compute(p_recv, "mb", lambda: ((p_recv["mb_enc"] - p_recv["k"]) % p_recv["N"]), "(m'_b - k) mod N")


if __name__ == "__main__":
    # ot_protocol = OT()

    # ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}, "Receiver": {"b": 1}})
    # s = time.time()
    # ot_protocol()
    # e = time.time()
    # print("OT time", e-s)
    # for role, stats in ot_protocol.get_party_statistics().items():
    #     print(role)
    #     print(stats)

    ot_protocol = OT()
    ot_protocol.set_party_addresses({"Sender": "127.0.0.1:4858", "Receiver": "127.0.0.1:4868"}, "Sender")
    ot_protocol.set_input({"Sender": {"m0": 21, "m1": 39}})
    ot_protocol()
    # for step in ot_protocol.protocol_steps:
    #     for opp in step.step_description:
    #         print(opp.__str__())

    print(ot_protocol.get_output())

    ot_protocol.terminate_protocol()