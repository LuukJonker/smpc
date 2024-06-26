# SMPC


## Installation guide

### Clone the repository

```bash
git clone https://github.com/LuukJonker/smpc.git
```

### Install Python

This project is compatible with Python 3.11 and above. You can download the latest version of Python from the official website: https://www.python.org/downloads/

To check the version of Python installed on your system, run the following command:
```bash
python3 --version
```

### Create a virtual environment

It is recommended to use a virtual environment to install the dependencies. To create a virtual environment, run the following command:

#### Windows

```bash
python -m venv venv
```

#### Linux or MacOS

```bash
python3 -m venv venv
```

To activate the virtual environment, run the following command:

#### Windows
```bash
venv\Scripts\activate
```

#### Linux or MacOS
```bash
source venv/bin/activate
```

### Install dependencies

Now that the virtual environment is activated, you can install the dependencies using the following command:

```bash
pip install -r requirements.txt
```

### Run the application

To run the gui, execute the following command from the root directory of the project:

```bash
python3 run.py implementedProtocols
```

### Upload SMPCbox package
To upload a new version to PyPI do the following:
First increment the version number in setup.py
Then run:
```bash
./uploadPyPI.bash
```
This will then prompt you to enter an API token for PyPI

