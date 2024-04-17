from SMPCbox.ProtocolComputation import ProtocolComputation
from typing import Any, Type

class ProtocolStep():
    def __init__(self, name: str):
        self.__step_name = name
        self.__step_description = []
    
    def run_computation (self, computation: Type[ProtocolComputation], local_variables: dict[str, Any], computed_variable_name: str = None):
        res = computation.execute_computation(local_variables)
        self.__step_description.append(computation.get_computation_description())

        if (computed_variable_name != None):
            local_variables[computed_variable_name] = res
            self.__step_description[-1] = f"{computed_variable_name} = {self.__step_description[-1]}"

    """
    get_step_description() -> (str, list[str])

    Returns a tuple containing the name of the step and the description of all the computations that have 
    been run using the run_computation function.
    """
    def get_step_description(self):
        return (self.__step_name, self.__step_description)
