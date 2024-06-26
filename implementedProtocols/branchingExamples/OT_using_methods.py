# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../../')

from SMPCbox import AbstractProtocol, local

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
        self.choose_xb()
        self.compute(p_recv, "v", lambda: ((p_recv["x_b"] + pow(p_recv["k"], p_recv["e"])) % p_recv["N"]), "(x_b + k^e) mod N")
        self.send_variables(p_recv, p_send, "v")

        # calculate the encrypted m0 and m1
        self.compute(p_send, "k0", lambda: pow(p_send["v"] - p_send["x0"], p_send["d"], p_send["N"]), "(v-x0)^d mod N")
        self.compute(p_send, "k1", lambda: pow(p_send["v"] - p_send["x1"], p_send["d"], p_send["N"]), "(v-x1)^d mod N")
        self.compute(p_send, "m0_enc", lambda: ((p_send["m0"] + p_send["k0"]) % p_send["N"]), "(m0 + k0) mod N")
        self.compute(p_send, "m1_enc", lambda: ((p_send["m1"] + p_send["k1"]) % p_send["N"]), "(m1 + k1) mod N")
        self.send_variables(p_send, p_recv, ["m0_enc", "m1_enc"])

        self.choose_mb_enc()
        self.compute(p_recv, "mb", lambda: ((p_recv["mb_enc"] - p_recv["k"]) % p_recv["N"]), "(m'_b - k) mod N")
    
    @local("Receiver")
    def choose_xb(self):
        if self.parties["Receiver"]["b"] == 0:
            self.compute(self.parties["Receiver"], "x_b", lambda: self.parties["Receiver"]["x0"], "x0")
        else:
            self.compute(self.parties["Receiver"], "x_b", lambda: self.parties["Receiver"]["x1"], "x1")
    

    @local("Receiver")
    def choose_mb_enc(self):
        if self.parties["Receiver"]["b"] == 0:
            self.compute(self.parties["Receiver"], "mb_enc", lambda: self.parties["Receiver"]["m0_enc"], "m0_enc")
        else:
            self.compute(self.parties["Receiver"], "mb_enc", lambda: self.parties["Receiver"]["m1_enc"], "m1_enc")



if __name__ == "__main__":
    ot_protocol = OT()

    # ot_protocol.set_input({"Sender": {"m0": 1, "m1": 29}, "Receiver": {"b": 1}})
    # s = time.time()
    # ot_protocol()
    # e = time.time()
    # print("OT time", e-s)
    # for role, stats in ot_protocol.get_party_statistics().items():
    #     print(role)
    #     print(stats)

    ot_protocol = OT()
    ot_protocol.set_party_addresses({"Sender": "127.0.0.1:4851", "Receiver": "127.0.0.1:4861"}, "Receiver")
    ot_protocol.set_input({"Receiver": {"b": 0}})
    ot_protocol()
    # for step in ot_protocol.protocol_steps:
    #     for opp in step.step_description:
    #         print(opp.__str__())

    print(ot_protocol.get_output())

    ot_protocol.terminate_protocol()