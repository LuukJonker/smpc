# implements the protocol from Gilboa1999 for multiplication

import time
from SMPCbox import AbstractProtocol
from OT import OT
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

    def get_expected_input(self):
        return {"Alice": ["a"], "Bob": ["b"]}

    def get_party_names(self) -> list[str]:
        return ["Alice", "Bob"]

    def output_variables(self) -> dict[str, list[str]]:
        return {"Alice": ["x"], "Bob": ["y"]}

    def __call__(self):
        self.add_protocol_step("Generate r")
        r_vars = ["r" + str(num) for num in range(self.l)]
        self.compute(self.parties["Alice"], r_vars, [], lambda: [rand_int() for _ in range(self.l)], "rand()")

        self.add_protocol_step("Perform l OTs")
        for i in range(self.l):
            # calculate a*2^i + r_i:
            self.compute(self.parties["Alice"], ["m1_input"], ["a", "r" + str(i)], lambda a, r_i: a * (2**i) + r_i, "a*2^i + r_i")
            # get ith bit of Bob's b variable
            self.compute(self.parties["Bob"], "b_i", "b", lambda b: (b >> i) & 1, "Determine b_i")

            ot_inputs = {"Sender": {"m0": "r"+str(i), "m1": "m1_input"}, "Receiver": {"b": "b_i"}}
            ot_output = {"Receiver": {"mb": f"m{i}_b{i}"}}
            self.run_subroutine_protocol(OT, {"Sender": self.parties["Alice"], "Receiver": self.parties["Bob"]}, ot_inputs, ot_output)

        self.add_protocol_step("Calculate outputs")
        self.compute(self.parties["Alice"], "x", r_vars, lambda *r_vals: -sum(r_vals), "- Sum of all r_i")

        exchanged_messages = [f"m{i}_b{i}" for i in range(self.l)]
        self.compute(self.parties["Bob"], "y", exchanged_messages, lambda *all_messages: sum(all_messages), "Sum of all mi_bi")


if __name__ == "__main__":
    # alice = ProtocolParty("Alice", "127.0.0.1:3299")
    # bob = ProtocolParty("Bob", "127.0.0.1:3300", is_listening_socket=False)
    # time.sleep(5)
    p = SecretShareMultiplication(l=32)
    # p.set_protocol_parties({"Alice": alice, "Bob": bob})
    # p.set_running_party("Alice", alice)
    p.set_input({"Alice": {"a": 21}, "Bob": {"b": 3289}})
    s = time.time()
    p()
    e = time.time()
    print("execution time:", e-s)
    out = p.get_output()
    for role, stats in p.get_statistics().items():
        print(role)
        print(stats)

    p.terminate_protocol()
    print(out)
    print("Shared secret (x+y):", out["Alice"]["x"] + out["Bob"]["y"] )


