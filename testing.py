from SMPCbox.ProtocolComputation import ProtocolComputation
from SMPCbox.ProtocolStep import ProtocolStep

if __name__ == "__main__":
    computation = ProtocolComputation(["a", "b", "c"], lambda x,y,z: x+y+z, "a + b + c")
    current_step = ProtocolStep("step 1")
    local_vars = {"a": 1, "b": 2, "c": 3}
    current_step.run_computation(computation, local_vars, "d")
    current_step.run_computation(computation, local_vars, "q")
    local_vars["x"] = "Hello "
    local_vars["y"] = "String "
    local_vars["z"] = "Computation "
    computation = ProtocolComputation(["x", "y", "z"], lambda x,y,z: x+y+z, "concat strings x, y, z")
    current_step.run_computation(computation, local_vars, computed_variable_name="result")
    computation = ProtocolComputation(["q"], lambda x: None, "send variable q")
    current_step.run_computation(None, computation, local_vars)
    print(local_vars)
    print(current_step.get_step_description())