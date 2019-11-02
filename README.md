# Medical Blockchain

A blockchain implemented to follow drugs supply chain. This project was made while doing my memoir at the [UTFSM](https://www.usm.cl/) in Valparaiso, Chile.
The back-end of the blockchain uses mainly Python, and specifically the [flask](https://palletsprojects.com/p/flask) framework.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements for the medical blockchain.

```bash
git clone https://github.com/joachimdorel/Medical-Blockchain.git
pip install --upgrade pip
pip install pip-tools
pip-sync # install the packages needed
```

## Usage

To launch the blockchain from a terminal, and the blockchain will run on port 5000:
```bash
cd Medical-Blockchain
source venv/bin/activate
export FLASK_APP=blockchain.py
flask run
```

Alternatively, the blockchain can run on any port with (here to run it on port 5001):
```bash
flask run -p 8001
```

From another terminal, you now need to launch the client of the blockchain:
```bash
cd Medical-Blockchain
source venv/bin/activate
export FLASK_APP=blockchain.py
python run_app.py
```

Alternatively, the client can run on any port with (here to run it on port 8001):
```bash
python run_app.py -p 5001
```

## License
[MIT](https://choosealicense.com/licenses/mit/)