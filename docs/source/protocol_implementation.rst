Implementing SMPC protocols
===========================


Creating a new your protocol class
----------------------------------

To implement new SMPC protocols users should create a new class which inherits from the ``AbstractProtocol`` class which can be imported from SMPCbox.
Below an example is shown of how this can be done and what methods need to be implemented:

.. code-block:: python

    from SMPCbox import AbstractProtocol

    class MyProtocol(AbstractProtocol):
        protocol_name="My protocol"

        def __init__(self):
            super().__init__()
        
        def party_names(self) -> list[str]:
            return ["Party1", "Party2"]

        def input_variables(self) -> dict[str, list[str]]:
            return {"Party1":["input_variable_1","input_variable_2"],"Party2":["input_variable"]}
        
        def output_variables(self) -> dict[str, list[str]]:
            return {"Party1": ["output_variable"]}
        
        def __call__(self):
            # Implement the protocol opperations here

Available methods
-----------------

With the ``AbstractProtocol`` your protocol class has also inherited a variety of usefull methods.
These methods can be used to implement your protocol. The execution of your protocol should be executed in its entirety when the ``__call__`` method is used.

Adding Local computations
~~~~~~~~~~~~~~~~~~~~~~~~~

bla bla

Sending and receiving variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

bla bla
