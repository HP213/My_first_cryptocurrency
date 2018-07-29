#Created on Mon Jul 23 05:51:30 2018
#modul2 - Create a Cryptocurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#part-1 Creating a blockchain

#definig a class(Because is is much better than creating a function)
class Blockchain:
    #creating a function to initialise blockchain
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
    #creating a block
    def create_block(self, proof, previous_hash):
        #definig a dictionary to create a block everytime 
        block = {'index' : len(self.chain) + 1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.transactions}
        self.chain.append(block)
        self.transactions = []
        return block
    
    #getting the last created block
    def get_prev_block(self):
        return self.chain[-1]
    
    #defining algorithm to solve the problem and also return proof
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    #Making a hash of given block
    def hash_value(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    #validating is whole chain is valid or not
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash_value(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    #ADD Transctions details to list of transactions before adding to blockchain
    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver': receiver,
                                  'amount' : amount})
        previous_block  = self.get_prev_block();
        return previous_block['index'] + 1
    
    #adding nodes from anywhere using different ports
    def add_nodes(self, address):
        parsed_address = urlparse(address)
        self.nodes.add(parsed_address.netloc)
    
    #replacing chain with longest chain
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['Length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain :
            self.chain = longest_chain
            return True
        return False
        
    
    #Part -2 Mining our Blockchain
    
 #creating a web app
app = Flask(__name__)
 
#Creating an address for node o n port 5000
node_address = str(uuid4()).replace('-', ' ')

 #creatinga blockchain 
blockchain = Blockchain()
 
 #Mining a new block
 
@app.route('/mine_block', methods = ['GET'])
def mine_block():
     previous_block = blockchain.get_prev_block()
     previous_proof = previous_block['proof']
     proof = blockchain.proof_of_work(previous_proof)
     previous_hash = blockchain.hash_value(previous_block)
     blockchain.add_transactions(sender = node_address, receiver = 'C', amount = 10)
     block = blockchain.create_block(proof, previous_hash)
     response = {'message' : 'Congratulations, You Just mined a block',
                 'index' : block['index'],
                 'timestamp' : block['timestamp'],
                 'proof' : block['proof'],
                 'previous_hash' : block['previous_hash'],
                 'transactions' : block['transactions']}
     return jsonify(response), 200
     
#Getting the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'Length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/chain_valid', methods = ['GET'])
def chain_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid :
        response = {'Message' : 'Chain is Valid!!!',
                'Length' : len(blockchain.chain)}
    else :
        response = {'Message' : 'Chain is not valid'}
    return jsonify(response), 200

#Adding new transaction to blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transactions(json['sender'], json['receiver'], json['amount'])
    response = {'message' : f'This transaction will be added to block {index}'}
    return jsonify(response), 201

#Part-3 Decentralising our Blockchain

#connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No NOde found', 400
    for node in nodes :
        blockchain.add_nodes(node)
    response = {'message' : 'All the nodes are now connected, The hadcoins contains :',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201

#Replacing or we can say updating the chain
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : "The chain was not updated, we have updated it",
                    'new_chain' : blockchain.chain}
    else:
        response = {'message' : 'The Chain is up-to-date',
                     'chain' : blockchain.chain}
    return jsonify(response), 200
    

#running the app
app.run(host = '0.0.0.0', port = 5003)