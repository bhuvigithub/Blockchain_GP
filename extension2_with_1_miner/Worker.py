#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 12:05:30 2021

@author: mininet
"""
from Blockchain import Blockchain
from Block import Block
from datetime import datetime
from flask import Flask,jsonify,abort,request
import json
import threading
import time
import requests
import sys
from uuid import getnode as get_mac
from random import randrange
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

class Worker:
    def __init__(self, host, port, mac, debug, IPs):
        # host: the Worker ip
        # port: the Worker port
        # debug: the Worker debug mode
        # IPs: the Miners' IP addresses
        self.host = host
        self.port = port
        self.mac = mac
        self.debug = False
        self.IPs = IPs
        # blockchain: Worker type blockchain
        self.blockchain = Blockchain('Worker')
        # Flask app creation of worker
        self.app = Flask(__name__)
        """ Generate private publick key"""
        self.private_key = RSA.generate(1024)
        self.public_key = self.private_key.public_key().export_key().decode()
        # Flask method1: View the blockchain on Worker by index.
        @self.app.route('/blockchains/<int:id>',methods=['GET'])
        def get_blockchains(id):
            data = {
                    'index': self.blockchain.blocks[id].index,
                    'timestamp': self.blockchain.blocks[id].timestamp,
                    'transaction': self.blockchain.blocks[id].transaction,
                    'previous_hash': self.blockchain.blocks[id].previous_hash,
                    'mac': self.blockchain.blocks[id].mac,
                    'hash': self.blockchain.blocks[id].hash
                    }
            return jsonify(data)
        # Flask app method2: Receiver of Miner, receive block from miners
        # After receiving block, it processes the block directly.
        @self.app.route('/workerReceiver', methods=['POST'])
        def receive_block():
            if not request.data:
                abort(400)
            str = request.data.decode('utf-8')
            str_json = json.loads(str)
            # Process the block
            self.process(str_json)
            return jsonify(str_json)
        # Start worker directly.
        self.start()
        
    # start contains main thread and a sub-thread.
    
    def start(self):
        time.sleep(1)
        #send public key to all miners
        self.send_public_key()
        
        # Start listen thread
        
        subthread = threading.Thread(target = self.listen)
        subthread.start()

        # Set a timeout for getting Genesis block
        time.sleep(10)
        # Generate blocks periodly on main thread
        while True:
            print("Worker while loop generate block.")
            # Generate and block to Miner.
            new_block = self.generate_block()
            signed_block = self.sign_block(new_block)

            # Send the block to all Miners.
            # in our following extension, may multiple Miners.

            for i in range(len(self.IPs)):
                url = 'http://' + self.IPs[i] + ':5000/minerReceiver'
                response = requests.post(url , data = signed_block)
                if i == 0:
                    print("New Generated Common Block content:")
                    print(response.content)

            time.sleep(15)
            
            
    def listen(self):
        print("Start sub-thread for listening. (Worker)")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True)
    # Generate a new block.
    def generate_block(self):
        index = len(self.blockchain.blocks)
        transactions = self.generate_transactions()

        new_block = Block(index,
                          str(datetime.now()),
                          transactions,
                          self.blockchain.blocks[index-1].hash,
                          self.mac
                          )

        return new_block
        
    #Generates a random number of transactions from this host to another random host
    def generate_transactions(self):
        number_of_transactions = randrange(5) + 1
        receiver_list = []
        own_id = int(self.mac[len(self.mac)-1])
        number_of_hosts = 5
        for i in range(number_of_hosts):
            id = i+1
            if(id != own_id):
                receiver_list.append('h'+str(id))

        transactions = []
        for x in range(number_of_transactions):
            transaction = {
                "sender" : "h" + str(own_id),
                "receiver" : receiver_list[randrange(number_of_hosts-1)],
                "amount" :  randrange(100) + 1
            }
            transactions.append(transaction)

        return transactions
            
    def process(self, str_json):
        "index, timestamp, transaction, previous_hash, mac"
        time = str_json['timestamp']
        transaction = str_json['transaction']
        mac = str_json['mac']
        
        if len(str_json) == 5:
            preHash = str_json['previous_hash']
            "can add a verify and return a result"
            # verify_block(?) 
            print("This Worker receives first block.")
            self.blockchain.add_blockG(time, transaction, preHash, mac)
        else:
            print("This Worker receives common block.")
            "can add a verify and return a result"
            # verify_block(?)
            self.blockchain.add_block(time, transaction, mac)
    
    #encryption using private key and creation of a JSON that can be sent to the miner
    def sign_block(self, block):
        json_block = str(block.__dict__)  #creates a JSON string from the object
        hash= SHA256.new(json_block.encode())
        signer=pkcs1_15.new(self.private_key)
        signature= signer.sign(hash).hex()

        signed_block = {
            "block" : json_block,
            "signature" : signature
        }

        signed_block_json = json.dumps(signed_block)
        return signed_block_json
        
    #Sends public key to the miners
    def send_public_key(self):
        key_json = {
            'pub_key': self.public_key,
        }
        for i in range(len(self.IPs)):
            url = 'http://' + self.IPs[i] + ':5000/key-receiver'
            response = requests.post(url , json = key_json)
            print(response.content)
    
if __name__ == '__main__':
    # Test mode
    """In basic version, just one Miner, in our first and second extension,
       more Miners are used, so that we can use an IP list as input.
    """
    #w = Worker('10.0.0.2', '5000','00:11:22:33:44:02', False, ['10.0.0.1'])
    macStr = '00:11:22:33:44:0' + sys.argv[1].split('.')[3] 
    print(sys.argv[1], sys.argv[2], str,sys.argv[3], sys.argv[4:])
    w = Worker(sys.argv[1], sys.argv[2], macStr,sys.argv[3], sys.argv[4:])
    # Combination mode
    "When we combine Starter.py, it can set the parameter."
   
    
    
    
