# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')

from SMPCbox import AbstractProtocol
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
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
        return {"Sender":["m1","m2"],"Receiver":["b"]}
    
    def get_party_roles(self) -> list[str]:
        return ["Sender", "Receiver"]
    
    def __call__(self):
        sender = self.parties["Sender"]
        receiver = self.parties["Receiver"]

        self.compute(sender, ["N", "d", "e"], [], getRSAvars, "RSA()")
        self.send_variables(sender, receiver, ["N", "e"])
        self.compute(sender, ["x1", "x2"], [], lambda: (os.urandom(16), os.urandom(16)), "rand()")
        self.send_variables(sender, receiver, ["x1", "x2"])
        self.compute(receiver, "k", [], lambda: os.urandom(16), "rand()")




        



if __name__ == "__main__":
    OT()