from SMPCbox.ProtocolComputation import ProtocolComputation


if __name__ == "__main__":
    computation = ProtocolComputation(["a", "b", "c"], lambda x,y,z: x+y+z, "a + b + c")
    print(computation.execute_computation({"a": 1, "b": 2, "c": 3}))