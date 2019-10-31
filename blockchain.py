from hashlib import sha256
import json

import time
from uuid import uuid4

import requests
from flask import Flask, jsonify, request, url_for

'''
Object block of the blockchain, composed of:
 - an index
 - a list of transactions
 - a timetstamp
 - the previous block's hash
 - a nonce
'''
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """
        #Order the dictionary by id indexes, to get consistent hash
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:

    #Difficulty of the proof of work
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        Function to generate the first block and the first hash
        """
        genesis_block = Block(0, [], time.time(), "00")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        """
        Proof of work's function that verify that the start of our hash is a
        number of zeros.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while computed_hash.startswith('0' * self.difficulty) is False:
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof):
        """
        Function to add a block to the chain
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and comply
        with the difficulty
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def check_chain_validity(cls, chain):
        """
        Check is the hash is correct or no
        """
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.hash) or previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        Function who add all the unconfirmed transactions to a block and
        getting then the proof of work
        """
        #if there is no transaction
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        announce_new_block(new_block)
        return new_block.index

# CREATION OF THE BLOCKCHAIN API
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

#This node copy of the Blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# A list of adress of all the other members of the network
peers = set()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required_fields = ["batch_id", "sender_id", "recipient_id", "quantity"]

    if not all(k in values for k in required_fields):
        return 'Missing values', 400

    batch_exist = False
    for block in blockchain.chain:
        for transaction in block.transactions:
            if int(transaction['batch_id']) == int(values['batch_id']):
                batch_exist = True

    if batch_exist is False:
        print("Medicine does not exist.")
        return 'The medicine does not exist in the blockchain', 400

    values["timestamp"] = time.time()
    values["status"] = "waiting"
    blockchain.add_new_transaction(values)

    response = {'message': 'Transaction will be added'}
    return jsonify(response), 201

@app.route('/response_transaction', methods=['POST'])
def response_transaction():
    values = request.get_json()
    required_fields = ["batch_id", "sender_id", "quantity", "recipient_id", "status"]

    if not all(k in values for k in required_fields):
        return 'Missing values', 400

    med_exist = False
    transaction_exist = False
    for block in blockchain.chain:
        for transaction in block.transactions:
            if transaction['batch_id'] == values['batch_id']:
                med_exist = True
            if transaction['batch_id'] == values['batch_id'] and transaction['sender_id'] == values['sender_id'] and transaction['recipient_id'] == values['recipient_id'] and transaction['status']:
                transaction_exist = True

    if med_exist is False:
        return 'The medicine does not exist in the blockchain', 400

    if transaction_exist is False:
        return 'The transaction does not exist in the blockchain', 400

    values["timestamp"] = time.time()
    blockchain.add_new_transaction(values)

    response = {'message': 'Transaction response has been added to the blockchain'}
    return jsonify(response), 201



@app.route('/register_batch', methods=['POST'])
def register_batch():
    """
    Case when a medicine producer wants to register a new batch
    """
    values = request.get_json()
    required_fields = ["batch_id", "sender_id", "quantity"]

    if not all(k in values for k in required_fields):
        return 'Missing values', 400

    values['recipient_id']=values['sender_id']
    values["timestamp"] = time.time()
    values["status"] = "accepted"
    blockchain.add_new_transaction(values)

    response = {'message': 'Medicine added to the blockchain'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def get_chain():
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    response = {
        "length": len(chain_data),
        "chain": chain_data,
        "peers": list(peers)
    }

    return jsonify(response), 200

@app.route('/mine', methods=['GET'])
def mine_transactions():
    result = blockchain.mine()
    if not result:
        response = {'message': 'No transaction to mine'}
    else:
        response = {'message': "Block #{} is mined.".format(result)}
    return jsonify(response), 200

@app.route('/unconfirmed_transactions', methods=['GET'])
def unconfirmed_transactions():
    return jsonify(blockchain.unconfirmed_transactions), 200

'''
-----
DECENTRALIZATION
-----
'''

'''
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201
'''

@app.route('/register_node', methods=['POST'])
def register_new_node():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Register this current node to another node
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code

def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            block.hash = block_data['hash']
            blockchain.chain.append(block)
    return blockchain


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


def consensus():
    """
    A simple consensus algorithm
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    Function to announce a new block to the others nodes
    """
    headers = {'Content-Type': "application/json"}
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)
