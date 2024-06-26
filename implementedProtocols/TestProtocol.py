# temporary for now to allow the import of the SMPCbox from the implementedProtocols
# folder. Should remove once it is pip installable
import sys
sys.path.append('../')

from SMPCbox import AbstractProtocol
import os
import random

def rand(num_bytes: int = 16):
    return int.from_bytes(os.urandom(num_bytes), 'big')

class Sum(AbstractProtocol):
    def __init__(self, num_parties: int):
        self.num_parties = num_parties
        super().__init__()

    def party_names(self) -> list[str]:
        return [f"party_{i}" for i in range(self.num_parties)]
    
    def input_variables(self) -> dict[str, list[str]]:
        input_vars = {}
        for name in self.party_names():
            input_vars[name] = ["value"]
        return input_vars
    
    def output_variables(self) -> dict[str, list[str]]:
        return {"party_0":["sum"]}
    
    def __call__(self):
        party_0 = self.parties["party_0"]
        self.compute(party_0, "r", rand, "rand()")
        self.compute(party_0, "accum", lambda: party_0["r"] + party_0["value"], "r + value")

        for i, name in enumerate(self.party_names()):
            if i == 0:
                continue

            prev_party = self.parties[self.party_names()[i-1]]
            cur_party = self.parties[name]
            self.send_variables(prev_party, cur_party, "accum")
            self.compute(cur_party, "accum", lambda: cur_party["accum"] + cur_party["value"], "accum + value")
        
        # the last party now has the total accumulation
        self.send_variables(self.parties[self.party_names()[-1]], self.parties["party_0"], "accum")
        self.compute(party_0, "sum", lambda: party_0["accum"] - party_0["r"], "accum - r")

if __name__ == "__main__":
    protocol = Sum(5)
    input = {}
    real_sum = 0
    for i in range(5):
        val = random.randint(10, 10000)
        input[f"party_{i}"] = {"value": val}
        real_sum += val
    # print(protocol.party_names(), protocol.input_variables(), protocol.output_variables())
    protocol.set_input(input)
    protocol()
    print(protocol.get_output())
    print("REAL:", real_sum)