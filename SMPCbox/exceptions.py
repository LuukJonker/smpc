from typing import Any

class SMPCboxError(Exception):
    """Base class of all custom Exceptions"""
    def __init__(self, message):
        super().__init__(message)

class InvalidProtocolInput(SMPCboxError):
    def __init__(self, party: str, missing_vars: list[str], invalid_provided_vars: list[str]):
        super().__init__(f"""'{party}' did not receive the correct input variables
                                Missing input variables: {missing_vars}
                                Provided non existing input variables: {invalid_provided_vars}""")

class InvalidVariableName(SMPCboxError):
    """
    The exception thrown when users try to create a variable which starts with and 
    underscore.
    """
    def __init__(self, variable_name: str):
        super().__init__(f"The variable name '{variable_name}' is not allowed")

class NonExistentVariable(SMPCboxError):
    def __init__(self, party: str, variable: str):
        super().__init__(f"'{party}' has no local variable named {variable}")

class IncorrectComputationResultDimension(SMPCboxError):
    def __init__(self, comp_description: str, res: Any, comp_var_len: int):
        super().__init__(f"The computation '{comp_description}' returns {res}, but is trying to assign {comp_var_len} variable(s)!")

class UnableToConnect(SMPCboxError):
    def __init__(self, ip: str, port: int):
        super().__init__(f"Unable to connect to party with listening address {ip}:{port}")

class VariableNotReceived(SMPCboxError):
    def __init__(self, sending_party: str, variable_name: str):
        super().__init__(f"The variable '{variable_name}' has not been received from party {sending_party}")

class InvalidLocalVariableAccess(SMPCboxError):
    def __init__(self, non_local_party: str, variable: str):
        super().__init__(f"Trying to access variable '{variable}' of non locally running party '{non_local_party}'")

class NonExistentParty(SMPCboxError):
    def __init__(self, protocol_name: str, party: str):
        super().__init__(f"The party '{party}' doesn't exist in the protocol '{protocol_name}'")

__all__ = ["SMPCboxError", "InvalidProtocolInput", "InvalidVariableName", "NonExistentVariable", 
           "IncorrectComputationResultDimension", "UnableToConnect", "VariableNotReceived",
           "InvalidLocalVariableAccess", "NonExistentParty"]