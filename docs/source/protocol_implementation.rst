Implementing SMPC protocols
===========================


Creating a new protocol class
-----------------------------

To implement new SMPC protocols users should create a new class which inherits from the ``AbstractProtocol`` class which can be imported from SMPCbox.
Your protocol needs to implement the following methods:

.. method:: self.party_names()
    :noindex:

    :returns: A list of party names. This list contains a string for each party in the protocol.
    :rtype: list[str]


.. method:: self.input_variables()
    :noindex:

    Defines what the expected input of the protocol will is.

    :returns: A dictionary which, for each party with input, contains a list of input variable names.
    :rtype: dict[str, list[str]]


.. method:: self.output_variables()
    :noindex:

    Defines what the output of the protocol will be. Note that each party should contain the specified local variables by the end of the protocol.

    :returns: A dictionary which, for each party with output, contains a list of output variable names.
    :rtype: dict[str, list[str]]

.. method:: self.__call__()
    :noindex:

    The ``__call__`` method should implement all the communication and computation steps of your protocol.

Lastly, one should make sure that the ``__init__`` method of the super class is also called!

Below an example is shown which implements all the mandatory methods (except the communication and computation steps):

.. code-block:: python

    from SMPCbox import AbstractProtocol

    class MyProtocol(AbstractProtocol):
        protocol_name="My protocol"

        def __init__(self):
            super().__init__()
        
        def party_names(self) -> list[str]:
            return ["Party1", "Party2"]

        def input_variables(self) -> dict[str, list[str]]:
            return {"Party1": ["input_variable_1", "input_variable_2"], "Party2": ["input_variable"]}
        
        def output_variables(self) -> dict[str, list[str]]:
            return {"Party1": ["output_variable"]}
        
        def __call__(self):
            # The communication and computation steps of the protocol should be defined here.
            pass


Defining communication and computation steps
------------------------------------------------

With the ``AbstractProtocol`` your protocol class has also inherits the methods needed to implement the computation and communication steps.
The execution of your protocol should be run in its entirety when the ``__call__`` method is used.
Note that, because the opperations for all the parties are done in one method, protocol implementers should only compute values using the methods provided by SMPCbox.


Retreiving parties
~~~~~~~~~~~~~~~~~~

To retreive a specific party of your protocol the attribute ``parties`` can be used.
This attribute is a dictionary with which a ProtocolParty instance of a specific party can be retrieved as follows:

.. code-block:: python

    self.parties['Party1']


Retreiving local variables
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important:: 
    Retreiving local variables within SMPCbox should be done with care. One should only access local variables within the computation of a call to the ``compute`` method. Apart from this protocol implementers should only access variables of parties they have made sure are local using the ``local`` method decorator or the ``is_local`` method.

A local variable of a party can be retreived as follows:

.. code-block:: python

    self.parties['Party1']['var_name']

Adding Local computations
~~~~~~~~~~~~~~~~~~~~~~~~~

To add local computations the following method should be used:

.. method:: self.compute(party, computed_vars, computation, description)
    :noindex:

    Defines a local computation of a specific party that is part of the protocol.

    :param party: The party that executes the protocol locally.
    :type party: ProtocolParty

    :param computed_vars: The variable name (s) for the value(s) that are returned from the computation
    :type computed_vars: Union[str, list[str]]

    :param computation: A function object that runs the computation when called.
    :type computation: Callable

    :param description: A string that is used in the visualisation that explains what the computation does.
    :type description: str

The above method can be used within the ``__call__`` method as follows:

**Setting a single variable**

.. code-block:: python

    self.compute(self.parties['Alice'], "c", lambda: self.parties['Alice']['a'] + self.parties['Alice']['b'], "a + b")


**Setting a multiple variable**

.. code-block:: python

    self.compute(self.parties['Alice'], ["a_inc", "b_inc"], lambda: (self.parties['Alice']['a'] + 1, self.parties['Alice']['b'] + 1), "(a + 1, b + 1)")

When setting multiple variables the protocol implementer should ensure that the number of given computed_vars is the same as the length the return of the computation.


Note how in the above examples only uses local variables of the party ``'Alice'`` in the computation.

Sending and receiving variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To send variables between parties the following methods are available.

.. method:: self.send_variables(sender, receiver, variables)
    :noindex:

    Defines a send opperation in which the variables are send from the sender to the receiver.

    :param sender: The party sending the variables who has the variables as local variables.
    :type sender: ProtocolParty

    :param receiver: The party receiving the variables. This party will have the specified variables as local variables after the call to this method.
    :type receiver: ProtocolParty

    :param variables: One or more local variables of the sender to send to the receiver.
    :type variables: Union[str, list[str]]

**Example with a single variable**

.. code-block:: python

    self.send_variables(self.parties['Alice'], self.parties['Bob'], 'variable1')

**Example with multiple variables**

.. code-block:: python

    self.send_variables(self.parties['Alice'], self.parties['Bob'], ['variable1', 'variable2', 'variable3'])

.. method:: self.broadcast_variables(broadcasting_party, variables)
    :noindex:

    Defines a broadcast opperation. After this call the local variables specified are known to every party in the protocol.
    Currently this has been implemented as a seperate send opperation to each party of the protocol.

    :param broadcasting_party: The party broadcasting the variables who has the variables as local variables.
    :type sender: ProtocolParty

    :param variables: One or more local variables of the sender to broadcast to all other parties.
    :type variables: Union[str, list[str]]

**Example with a single variable**

.. code-block:: python

    self.broadcast_variables(self.parties['Alice'], 'variable1')

**Example with multiple variables**

.. code-block:: python

    self.broadcast_variables(self.parties['Alice'], ['variable1', 'variable2', 'variable3'])

After a call to the above methods a receiving party has the send variables as local variables.
The receiving of variables is handled by SMPCbox in a way which minimizes the time spent blocking to wait on unreceived variables.
The receiving party doesn't wait on a variable untill the variable is retreived. For optimal perfomance, protocol implementers should thus order their computations
in a way which waits as long as possible to access variables that are received from another party. 

Accessing local variables
~~~~~~~~~~~~~~~~~~~~~~~~~

Though not recomended in most cases SMPCbox does provide two ways for protocol implementers to safely access the values of local variables of a party outside of the computation
provided to the ``compute`` method. In some cases doing so can be necessary to perform branching or other control flow depending on a local variable.

Using the ``is_local`` method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. method:: self.is_local(party)
    :noindex:

    Allows protocol implementers to ensure a party is local in a certain code block.

    :param party: The party
    :type sender: ProtocolParty

    :rtype: boolean

Using the ``@local`` method decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


