import sys
sys.path.append('../')

from implementedProtocols.Sum import Sum
import unittest
from test_input import test_distributed, test_simulated

class TestSum(unittest.TestCase):
    def create_case(self, values):
        input = {}
        for i, val in enumerate(values):
            input[f"party_{i}"] = {"value": val}
        return input

    def cases(self):
        return [
            [0, 0],
            [0, 0, 0, 0],
            [12, 391, 12, 391],
            [5, -5],
            [1, 2, 3, 4, 5],
            [999, -999],
            [2**10, -2**10],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [-50, 50, -50, 50],
            [0, -1, -2, -3, -4, -5],
            [2**20, -2**20],
            [123456789, -123456789],
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10],
            [15, 30, 45, 60, 75, 90, 105],
            [-10, 0, 10, -20, 20, -30, 30],
            [2**30, -2**30],
            [0, 1] * 25,
            [-1, 0] * 25,
            [500] * 50,
            [-1000] * 50,
            [2**40, -2**40],
            [7, 14, 21, 28, 35, 42, 49, 56, 63, 70] * 5 + [329832**12] + [-1328**11, 3282] *2,
            [-100, -200, -300, -400, -500, -600, -700, -800, -900, -1000],
            [2**50, -2**50],
            [9, 18, 27, 36, 45, 54, 63, 72, 81, 90],
            [-5, -10, -15, -20, -25, -30, -35, -40, -45, -50],
            [2**60, -2**60],
            [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            [-3, -6, -9, -12, -15, -18, -21, -24, -27, -30],
            [2**70, -2**70],
            [1000, 2000, 3000, 4000, 5000],
            [-2, -4, -6, -8, -10],
            [123, -123, 456, -456],
            [2**80, -2**80],
            [42, -42, 84, -84],
            [7, 7, 7, 7, 7, 7, 7],
            [21, -21, 42, -42, 63, -63],
            [2**90, -2**90],
            [8, 16, 24, 32, 40, 48, 56, 64, 72, 80],
            [-2, 2, -4, 4, -6, 6, -8, 8, -10, 10],
            [333, -333, 666, -666, 999, -999],
            [2**100, -2**100],
            [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500],
            [-5, -10, -15, -20, -25],
            [12, 24, 36, 48, 60, 72, 84, 96, 108, 120],
            [-6, -12, -18, -24, -30, -36, -42, -48, -54, -60],
            [2**110, -2**110],
        ]

    def check_output(self, case, output):
        """
        Checks if the sum is correct
        """
        self.assertEqual(sum(case), output["party_0"]["sum"])

    
    def test_cases_distributed(self):
        start_port = 10000
        for case in self.cases():
            input = self.create_case(case)
            num_parties = len(case)
            out = test_distributed(Sum, input, start_port, init_args=[num_parties])
            self.check_output(case, out)
            start_port += 2
        print("Finished all 50 distributed tests")
    
    def test_cases_simulated(self):
        for case in self.cases():
            input = self.create_case(case)
            num_parties = len(case)
            out = test_simulated(Sum, input, init_args=[num_parties])
            self.check_output(input, out)
        print("Finished all 50 simulated tests")

if __name__ == "__main__":
    unittest.main()