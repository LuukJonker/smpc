from setuptools import setup, find_packages

LONG_DESCRIPTION = """
SMPCbox is a framework which can be used to implement Secure Multi Party Computation (SMPC) protocols.
The idea behind the project is to provide a way to easily test protocols, visualise protocol execution
and gather statistics on protocol execution.
This framework is meant to help researchers and students to better understand SMPC protocols.
"""

setup(name='SMPCbox',
      version='1.0.6',
      description='A framework for implementation of secure multi party computation protocols',
      author='Bas Jansweijer, Luuk Jonker, Zoltan Mann',
      author_email='bas.jansweijer@student.uva.nl, luuk.jonker@student.uva.nl',
      long_description=LONG_DESCRIPTION,
      packages=find_packages(),
    #   url='https://www.python.org/sigs/distutils-sig/',
      keywords=['python', 'protocols', 'multi party computation', 'MPC', 'secure multi party computation', 'SMPC']
     )