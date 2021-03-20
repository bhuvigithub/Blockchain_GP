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
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

key_path='/home/mininet/Desktop/file/final_implementation/encryption/host'
cert_path='/home/mininet/Desktop/file/final_implementation/encryption/host'

class Worker:
    def __init__(self, host, port, debug, IPs):
        # host: the Worker ip
        # port: the Worker port
        # debug: the Worker debug mode
        # IPs: the Miners' IP addresses
        self.host = host
        self.port = port
        self.debug = False
        self.IPs = IPs
        self.ID = int(self.host.split('.')[3])
        # blockchain: Worker type blockchain
        self.blockchain = Blockchain('Worker')
        # Flask app creation of worker
        self.app = Flask(__name__)
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
        # Start listen thread
        subthread = threading.Thread(target = self.listen)
        subthread.start()
        
        # Set a timeout for getting Genesis block
        time.sleep(12)
        # Generate blocks periodly on main thread
        while True:
            print("Worker while loop generate block.")
            # Generate and block to Miner.
            new_block = self.generate_block()
            data = {
                    'timestamp': new_block.timestamp,
                    'transaction': new_block.transaction,
                    'mac': new_block.mac
                    }
            # Send the block to all Miners.
            # in our following extension, may multiple Miners.
            for i in range(len(self.IPs)):
                url = 'https://' + self.IPs[i] + ':5000/minerReceiver'
                response = requests.post(url , data = json.dumps(data), verify=False)
                if i == 0:
                    print("New Generated Common Block content:")
                    print(response.content)

            time.sleep(15)
            
            
    def listen(self):
        print("Start sub-thread for listening. (Worker)")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True,
                     ssl_context=(cert_path + str(self.ID)+"/cert.pem",key_path+ str(self.ID)+ "/key.pem"))
    # Generate a new block.
    def generate_block(self):
        index = len(self.blockchain.blocks)
        """index,"""
        # When a new block is generated, the basic info sent is
        # timestamp, transaction, and uuid of this worker.
        """ index, previous hash and hash are used after verification."""
        new_block = Block(index,
                          str(datetime.now()),
                          'Block_transaction',
                          self.blockchain.blocks[index-1].hash,
                          'Worker_MAC(uuid)'
                     )
        return new_block
            
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
    
    "Thomas public key decyption"
    def verify_block(self, block):
        pass
    
if __name__ == '__main__':
    # Test mode
    """In basic version, just one Miner, in our first and second extension,
       more Miners are used, so that we can use an IP list as input.
    """
   # w = Worker('10.0.0.2', '5000', False, ['10.0.0.1'])
    
    # Combination mode
    "When we combine Starter.py, it can set the parameter."
    #print(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    w = Worker(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    
    
    
