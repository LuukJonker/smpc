from typing import Any, Union, Callable

class ProtocolStep():
    def __init__(self, name: str):
        self.__step_name = name
        self.__step_description = []
        
    def run_computation (self, computed_vars: list[str],  input_values: list[Any], computation: Callable, local_variables: dict[str, Any], description: str):
        
        # get the local variables
        res = computation(*input_values)

        if len(computed_vars) == 1:
            local_variables[computed_vars[0]] = res
            return
        
        if len(res) != len(computed_vars):
            raise Exception (f"The computation with description \"{description}\" returns {len(res)} output value(s), but is trying to assign to {len(computed_vars)} variable(s)!")

        self.__step_description.append(f"{', '.join([var for var in computed_vars])} = {description}")
        for i, var in enumerate(computed_vars):
            local_variables[var] = res[i]

    """
    get_step_description() -> (str, list[str])

    Returns a tuple containing the name of the step and the description of all the computations that have 
    been run using the run_computation function.
    """
    def get_step_description(self):
        return (self.__step_name, self.__step_description)
