Using the GUI
=============

Protocols that have been implemented can be used by the GUI as follows:


Using implemented protocols programatically
===========================================
In SMPCbox users can use the protocol class of an implemented protocol programatically.
The class of the protocol will be ``Protocol`` in the examples shown here. Note that in the examples we often call methods 
on an instance of this class that has been initialised as follows:

.. code-block:: python

    protocol = Protocol()


Protocol information
--------------------

The protocol class of an implemented protocol provides some key information on 
what the protocol expects when it comes to input and output.

To retreive information on what a protocol expects the following methods are available:

Participating parties
~~~~~~~~~~~~~~~~~~~~~

.. method:: protocol.party_names()
    :noindex:

    :returns: A list of party names. This list contains a string for each party in the protocol.
    :rtype: list[str]


Expected input of the protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: protocol.input_variables()
    :noindex:

    Defines what the expected input of the protocol will is.

    :returns: A dictionary which, for each party with input, contains a list of input variable names.
    :rtype: dict[str, list[str]]


Output of the protocol
~~~~~~~~~~~~~~~~~~~~~~

.. method:: protocol.output_variables()
    :noindex:

    Defines what the output of the protocol will be.

    :returns: A dictionary which, for each party with output, contains a list of output variable names.
    :rtype: dict[str, list[str]]


Running protocols
-----------------

To run the protocol class ``Protocol`` the following methods should be used:

.. method:: protocol.set_input(input)
    :noindex:

    Sets the provided input as the input of the protocol.

    :param input: The values of each input variable specified by the ``input_variables`` method.
    :type input: dict[str, dict[str, Any]]

.. method:: protocol()
    :noindex:

    This invokes the ``__call__`` method of the ``Protocol`` class which defines all the opperations of the protocol.
    Invoking this method will run the entire protocol. Note that this method cannot be used before the ``set_input`` method has been called.

.. method:: protocol.get_output()
    :noindex:

    Gets the output of the protocol, this method can be used after the protocol has been run.

    :returns: A dictionary which, for each party with output, contains a list of output variable names.
    :rtype: dict[str, list[str]]

Note that a single instance of a protocol class should only be used for one run of the protocol. If you want to run a protocol multiple times, we recomend using a fresh instance of the ``Protocol`` class each time.

Example Protocol
~~~~~~~~~~~~~~~~

In the following examples for simulated and distributed execution, the protocol class ``ExampleProtocol`` is used.
This class returns the following for the ``party_names``, ``input_variables``, and ``output_variables`` methods.

+------------------------+-----------------------------------------------------------+
| Method                 | Output                                                    |
+========================+===========================================================+
| ``party_names``        | ``['Alice', 'Bob']``                                      |
+------------------------+-----------------------------------------------------------+
| ``input_variables``    | ``{'Alice': ['var1', 'var2'], 'Bob': ['var3']}``          |
+------------------------+-----------------------------------------------------------+
| ``output_variables``   | ``{'Alice': ['result1'], 'Bob': ['result2', 'result3']}`` |
+------------------------+-----------------------------------------------------------+


Simulated execution
~~~~~~~~~~~~~~~~~~~

Execution of the ``ExampleProtocol`` can be done as follows:

.. code-block:: python

    exampleProtocol = ExampleProtocol()
    exampleProtocol.set_input({'Alice': {'var1': 1, 'var2': 2}, 'Bob': {'var3': 3}})
    exampleProtocol()
    print(exampleProtocol.get_output())

Output:

.. code-block:: python

    {'Alice': {'result1': 1}, 'Bob': {'result2': 2, 'result3': 3}}

Distributed execution
~~~~~~~~~~~~~~~~~~~~~

For distributed execution the following method also needs to be called:

.. method:: protocol.set_party_addresses(addresses, local_party)
    :noindex:

    Configures the protocol to run distributed with one party execution locally.

    :param addresses: The address (IP, port) for each party in the protocol
    :type addresses: dict[str, str]

    :param local_party: The name of the party that executes locally.
    :type local_party: str

Execution of the ``ExampleProtocol`` can then be done as follows:


.. code-block:: python

    exampleProtocol = ExampleProtocol()
    exampleProtocol.set_party_addresses({'Alice': '127.0.0.1:4000', 'Bob': '127.0.0.1:4001'}, 'Alice')
    exampleProtocol.set_input({'Alice': {'var1': 1, 'var2': 2}})
    exampleProtocol()
    print(exampleProtocol.get_output())

Output:

.. code-block:: python

    {'Alice': {'result1': 1}}

Note how the protocol is run with ``'Alice'`` as the local party. The provided input and output thus only
includes the input and output for ``'Alice'``.


Retreiving statistics
---------------------

After running a protocol statistics on the execution of the protocol can be retreived.
For this there are two methods:


.. method:: protocol.get_party_statistics()
    :noindex:

    Returns a set of statistics for each locally executed party.

    :return: A dictionary with the TrackedStatistics for each party.
    :rtype: dict[str, TrackedStatistics]


.. method:: protocol.get_total_statistics()
    :noindex:

    Returns the sum of the statistics of all the parties.

    :return: The summed statistics of all the local parties.
    :rtype: TrackedStatistics

The statistics can only be retreived after the protocol is run.

The TrackedStatistics object has the following attributes:


+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| Attribute              | Measured Statistic                                                                                                                        |
+========================+===========================================================================================================================================+
| ``execution_time``     | The sum of the wall clock time measured for each of the computations provided using the ``compute`` method.                               |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``execution_CPU_time`` | The sum of the CPU time measured for each of the computations provided using the ``compute`` method.                                      |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``wait_time``          | The time spend blocking to wait on variables that have not yet been received form other parties. (only relevant in distributed execution) |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``messages_send``      | The number of messages send (by a specific party). (Not the same as the number of sent variables)                                         |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``messages_received``  | The number of messages received (by a specific party). (Not the same as the number of received variables)                                 |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``bytes_send``         | The number of bytes send (by a specific party). This measures only the memory size of the content of each sent variable.                  |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+
| ``bytes_received``     | The number of bytes received (by a specific party). This measures only the memory size of the content of each received variable.          |
+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+

There are still some statistics which might be added in the future. For example:

* Number of sent variables
* Number of received variables
* A better measurement of the execution time of the whole protocol (t_start to t_end instead of the sum of all the parties execution times).
* Energy consumption