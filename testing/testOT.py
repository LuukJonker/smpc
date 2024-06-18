import sys
sys.path.append('../')

from implementedProtocols.OT import OT
import unittest
from test_input import test_distributed, test_simulated

class TestOT(unittest.TestCase):
    def cases(self):
        return [
            {"Sender": {"m0": 19, "m1": 28}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -19, "m1": -28}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -320949032819, "m1": -2324903240943891288}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -320942348342983893248 ** 12, "m1": -2324903240943891288 ** 30}, "Receiver": {"b": 2}},
            {"Sender": {"m0": 489754134842389 ** 33, "m1": 4138783491134 ** 33}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 0, "m1": -1}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 0, "m1": -1}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -1, "m1": 0}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -1, "m1": 0}, "Receiver": {"b": 2}},
            {"Sender": {"m0": 123, "m1": 456}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 789, "m1": 101112}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -987, "m1": -654}, "Receiver": {"b": 2}},
            {"Sender": {"m0": -321, "m1": -123}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 456789123, "m1": 123456789}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 1122334455, "m1": 5566778899}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 999999999, "m1": 888888888}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 777777777, "m1": 666666666}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -123456789, "m1": -987654321}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -111111111, "m1": -222222222}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 555555555, "m1": 444444444}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 333333333, "m1": 222222222}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 111111111, "m1": -111111111}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -222222222, "m1": 222222222}, "Receiver": {"b": 2}},
            {"Sender": {"m0": 333333333, "m1": -333333333}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -444444444, "m1": 444444444}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 555555555, "m1": -555555555}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -666666666, "m1": 666666666}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 777777777, "m1": -777777777}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -888888888, "m1": 888888888}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 999999999, "m1": -999999999}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -123, "m1": 456}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -789, "m1": 101112}, "Receiver": {"b": 2}},
            {"Sender": {"m0": 987, "m1": -654}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 321, "m1": -123}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -456789123, "m1": 123456789}, "Receiver": {"b": 3}},
            {"Sender": {"m0": -1122334455, "m1": 5566778899}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -999999999, "m1": 888888888}, "Receiver": {"b": 0}},
            {"Sender": {"m0": -777777777, "m1": 666666666}, "Receiver": {"b": 2}},
            {"Sender": {"m0": -123456789, "m1": 987654321}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -111111111, "m1": 222222222}, "Receiver": {"b": 3}},
            {"Sender": {"m0": -555555555, "m1": 444444444}, "Receiver": {"b": 1}},
            {"Sender": {"m0": -333333333, "m1": 222222222}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 987654321, "m1": 123456789}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 112233445566, "m1": 223344556677}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 998877665544, "m1": 887766554433}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 776655443322, "m1": 665544332211}, "Receiver": {"b": 0}},
            {"Sender": {"m0": 12345, "m1": 54321}, "Receiver": {"b": 2}},
            {"Sender": {"m0": 67890, "m1": 98765}, "Receiver": {"b": 1}},
            {"Sender": {"m0": 11111, "m1": 22222}, "Receiver": {"b": 3}},
            {"Sender": {"m0": 1849179484315**32, "m1": 22222**34}, "Receiver": {"b": 1}}
        ]
    

    def check_output(self, input, output):
        """
        Checks if the correct mb is returned
        I.E if it is m0/m1 mod N
        """
        mb = output["Receiver"]["mb"]
        b = input["Receiver"]["b"]
        if b == 0:
            self.assertEqual(mb, input["Sender"]["m0"] % output["Sender"]["N"])
        else:
            self.assertEqual(mb, input["Sender"]["m1"] % output["Sender"]["N"])

    
    def test_cases_distributed(self):
        start_port = 12000
        for input in self.cases():
            out = test_distributed(OT, input, start_port, extra_return_vars={"Sender": ["N"]})
            self.check_output(input, out)
            start_port += 2
        print("Finished all 50 distributed tests")
    
    def test_cases_simulated(self):
        for input in self.cases():
            out = test_simulated(OT, input, extra_return_vars={"Sender": ["N"]})
            self.check_output(input, out)
        print("Finished all 50 simulated tests")

if __name__ == "__main__":
    unittest.main()