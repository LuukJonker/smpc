from typing import Callable, Any

class ProtocolComputation ():
    def __init__ (self, arguments: list[str], computation: Callable[..., Any], description: str):
        self.description = description
        self.arguments = arguments
        self.computation = computation
    
    def execute_computation(self, local_variables: dict[str, Any]) -> Any:
        return self.computation(*[local_variables[arg] for arg in self.arguments])
    
    def get_computation_description(self) -> str:
        return self.description
    

