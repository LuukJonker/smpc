# implements the protocol from Gilboa1999 for multiplication
# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')


import time
from SMPCbox import AbstractProtocol
from implementedProtocols.OT import OT
import os

def rand_int():
    return int.from_bytes(os.urandom(2), byteorder='big')

class SecretShareMultiplication(AbstractProtocol):
    protocol_name = "SecretShareMultiplication"

    def __init__(self, l=32):
        """
        The opperations are done module 2^l
        """
        self.l = l
        super().__init__()

    def input_variables(self):
        return {"Alice": ["a"], "Bob": ["b"]}

    def party_names(self) -> list[str]:
        return ["Alice", "Bob"]

    def output_variables(self) -> dict[str, list[str]]:
        return {"Alice": ["x"], "Bob": ["y"]}

    def __call__(self):
        r_vars = ["r" + str(num) for num in range(self.l)]
        self.compute(self.parties["Alice"], r_vars, lambda: [rand_int() % pow(2, self.l) for _ in range(self.l)], "rand()")

        bob = self.parties["Bob"]
        alice = self.parties["Alice"]

        for i in range(self.l):
            # calculate a*2^i + r_i:
            self.compute(alice, ["m1_input"], lambda: (alice["a"] * (2**i) + alice["r" + str(i)]) % pow(2, self.l), "a*2^i + r_i")
            # get ith bit of Bob's b variable
            self.compute(bob, "b_i", lambda: (bob["b"] >> i) & 1, "Determine b_i")

            ot_inputs = {"Sender": {"m0": "r"+str(i), "m1": "m1_input"}, "Receiver": {"b": "b_i"}}
            ot_output = {"Receiver": {"mb": f"m{i}_b{i}"}}
            self.run_subroutine_protocol(OT(), {"Sender": self.parties["Alice"], "Receiver": self.parties["Bob"]}, ot_inputs, ot_output)

        self.compute(alice, "x", lambda: (-sum(alice[var] for var in r_vars)) % pow(2, self.l), "minus Sum of all r_i")

        exchanged_messages = [f"m{i}_b{i}" for i in range(self.l)]
        self.compute(bob, "y", lambda: (sum([bob[var] for var in exchanged_messages])) % pow(2, self.l), "Sum of all mi_bi")


if __name__ == "__main__":
    p = SecretShareMultiplication(l=32)

    p.set_party_addresses({"Bob": "127.0.0.1:4852", "Alice": "127.0.0.1:4862"}, "Alice")
    p.set_input({"Alice": {"a": 21}})
    s = time.time()
    p()
    e = time.time()
    print("execution time:", e-s)
    out = p.get_output()
    for role, stats in p.get_party_statistics().items():
        print(role)
        print(stats)

    p.terminate_protocol()
    print(out)
    # print("Shared secret (x+y):", (out["Alice"]["x"] + out["Bob"]["y"] ) % pow(2, 32))


