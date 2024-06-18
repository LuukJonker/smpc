import sys
sys.path.append('../')

from implementedProtocols.MultiplicationProtocol import SecretShareMultiplication
import unittest
from test_input import test_distributed, test_simulated

class TestMult(unittest.TestCase):
    def cases(self):
        return [
            {"Alice": {"a": 0}, "Bob": {"b": 0}, "Setting": {"l": 32}},
            {"Alice": {"a": 57}, "Bob": {"b": -123}, "Setting": {"l": 32}},
            {"Alice": {"a": -999}, "Bob": {"b": 1583}, "Setting": {"l": 45}},
            {"Alice": {"a": 32768}, "Bob": {"b": -15625}, "Setting": {"l": 30}},
            {"Alice": {"a": 123456}, "Bob": {"b": 234567}, "Setting": {"l": 35}},
            {"Alice": {"a": -60466176}, "Bob": {"b": 125000}, "Setting": {"l": 28}},
            {"Alice": {"a": 5625}, "Bob": {"b": -512000}, "Setting": {"l": 40}},
            {"Alice": {"a": 147258 ** 12}, "Bob": {"b": -963852 ** 11}, "Setting": {"l": 32}},
            {"Alice": {"a": 125000000}, "Bob": {"b": -125000}, "Setting": {"l": 36}},
            {"Alice": {"a": 2744000}, "Bob": {"b": -911250}, "Setting": {"l": 29}},
            {"Alice": {"a": 0}, "Bob": {"b": 1000000}, "Setting": {"l": 32}},
            {"Alice": {"a": -100000}, "Bob": {"b": -8000000}, "Setting": {"l": 31}},
            {"Alice": {"a": 1500625}, "Bob": {"b": 857375}, "Setting": {"l": 32}},
            {"Alice": {"a": -60466176 **17}, "Bob": {"b": 1500000**17}, "Setting": {"l": 30}},
            {"Alice": {"a": 837465}, "Bob": {"b": -750000}, "Setting": {"l": 32}},
            {"Alice": {"a": -562500}, "Bob": {"b": 157500}, "Setting": {"l": 38}},
            {"Alice": {"a": 73850}, "Bob": {"b": -145960}, "Setting": {"l": 25}},
            {"Alice": {"a": 8000000}, "Bob": {"b": -9630}, "Setting": {"l": 32}},
            {"Alice": {"a": 578943}, "Bob": {"b": 459456}, "Setting": {"l": 34}},
            {"Alice": {"a": -1296000}, "Bob": {"b": 823200}, "Setting": {"l": 30}},
            {"Alice": {"a": 921600}, "Bob": {"b": -1953125}, "Setting": {"l": 37}},
            {"Alice": {"a": 132743}, "Bob": {"b": 2731}, "Setting": {"l": 32}},
            {"Alice": {"a": 32768000}, "Bob": {"b": -22674816}, "Setting": {"l": 40}},
            {"Alice": {"a": 1000000000}, "Bob": {"b": 2000000000}, "Setting": {"l": 32}},
            {"Alice": {"a": -4826809}, "Bob": {"b": 5764801}, "Setting": {"l": 28}},
            {"Alice": {"a": 768320}, "Bob": {"b": -923780}, "Setting": {"l": 33}},
            {"Alice": {"a": 45612}, "Bob": {"b": 78923}, "Setting": {"l": 30}},
            {"Alice": {"a": -850125}, "Bob": {"b": 965344}, "Setting": {"l": 32}},
            {"Alice": {"a": 82403}, "Bob": {"b": -12903}, "Setting": {"l": 27}},
            {"Alice": {"a": 100234}, "Bob": {"b": 723451}, "Setting": {"l": 39}},
            {"Alice": {"a": -6539200}, "Bob": {"b": -190873}, "Setting": {"l": 29}},
            {"Alice": {"a": 92412}, "Bob": {"b": 12345}, "Setting": {"l": 32}},
            {"Alice": {"a": 111111}, "Bob": {"b": 234567}, "Setting": {"l": 32}},
            {"Alice": {"a": 234500}, "Bob": {"b": -500000}, "Setting": {"l": 30}},
            {"Alice": {"a": 1001125}, "Bob": {"b": 234543}, "Setting": {"l": 33}},
            {"Alice": {"a": -1024000}, "Bob": {"b": 17895697}, "Setting": {"l": 32}},
            {"Alice": {"a": 154878}, "Bob": {"b": -25473}, "Setting": {"l": 32}},
            {"Alice": {"a": 1789785}, "Bob": {"b": -120003}, "Setting": {"l": 26}},
            {"Alice": {"a": 888888}, "Bob": {"b": -999999}, "Setting": {"l": 32}},
            {"Alice": {"a": 55321}, "Bob": {"b": -43210}, "Setting": {"l": 30}},
            {"Alice": {"a": 1284375}, "Bob": {"b": 1309375}, "Setting": {"l": 32}},
            {"Alice": {"a": -1450000}, "Bob": {"b": 1837465}, "Setting": {"l": 35}},
            {"Alice": {"a": 9473567}, "Bob": {"b": 1908731}, "Setting": {"l": 32}},
            {"Alice": {"a": 327680}, "Bob": {"b": -2267}, "Setting": {"l": 37}},
            {"Alice": {"a": 3000000}, "Bob": {"b": 4000000}, "Setting": {"l": 28}},
            {"Alice": {"a": -1029384}, "Bob": {"b": 2038400}, "Setting": {"l": 32}},
            {"Alice": {"a": 505000000}, "Bob": {"b": -603000000}, "Setting": {"l": 34}},
            {"Alice": {"a": 109437}, "Bob": {"b": 218563}, "Setting": {"l": 32}},
            {"Alice": {"a": 7000125}, "Bob": {"b": 8000000}, "Setting": {"l": 33}}
        ]

    

    def check_output(self, input, output, l):
        """
        Checks if a correct x and y are returned.
        I.E. if (x + y) mod 2**l = (a * b) mod 2**l
        """
        out = (output["Alice"]["x"] + output["Bob"]["y"]) % (2**l)
        expected_out = (input["Alice"]["a"] * input["Bob"]["b"]) % (2**l)
        self.assertEqual(out, expected_out)

    
    def test_cases_distributed(self):
        i = 0
        start_port = 10000
        for input in self.cases():
            l = input["Setting"]["l"]
            del input["Setting"]
            out = test_distributed(SecretShareMultiplication, input, start_port, init_args=[l])
            self.check_output(input, out, l)
            start_port += 2
            i += 1
            print("Finished case", i)
        print("Finished all 50 distributed tests")
    
    def test_cases_simulated(self):
        i = 0
        for input in self.cases():
            l = input["Setting"]["l"]
            del input["Setting"]
            out = test_simulated(SecretShareMultiplication, input, init_args=[l])
            self.check_output(input, out, l)
            i += 1
            print("Finished case", i)
        print("Finished all 50 simulated tests")

if __name__ == "__main__":
    unittest.main()