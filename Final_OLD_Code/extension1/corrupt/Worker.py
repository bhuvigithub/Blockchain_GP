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
import random
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
        self.compareList = []
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
        print(self.IPs)
        time.sleep(1)
        #send public key to all miners
        self.send_public_key()
        
        # Start listen thread
        time.sleep(1)
        subthread = threading.Thread(target = self.listen)
        subthread.start()
        
        subthread2 = threading.Thread(target = self.verifyLoop)
        subthread2.start()
        # Set a timeout for getting Genesis block
        time.sleep(10)
        # Generate blocks periodly on main thread
        while True:
            print("Worker while loop generate block.")
            self.randomSleep()
            # Generate and block to Miner.
            new_block = self.generate_block()
            signed_block = self.sign_block(new_block)

            # Send the block to all Miners.
            # in our following extension, may multiple Miners.

            for i in range(len(self.IPs)):
                url = 'http://' + self.IPs[i] + ':5000/minerReceiver'
                print(url)
                response = requests.post(url , data = signed_block)
                if i == 0:
                    print("New Generated Common Block content:")
                    print(response.content)
            
    def verifyLoop(self):
        print('Sub2 begin')
        time.sleep(10)
        while True:
            self.verify_block()
            time.sleep(5)
    def randomSleep(self):
        t = random.randint(3, 30)
        print(t)
        
        time.sleep(t)
        
    def verify_block(self):
        process_size = len(self.IPs)
        max_list = []
        if len(self.compareList) > process_size:
            get_size = 0
            for i in self.compareList:
                if get_size <= process_size:
                    max_list.append(i)
                    get_size = get_size + 1
            for i in range(process_size):         
                del(self.compareList[0])
            max_block = (max(max_list, key = max_list.count))
            print("Correct Block" + str(max_block))
            self.blockchain.add_block(max_block['timestamp'], max_block['transaction'], max_block["mac"]) 
            
    def listen(self):
        print("Start sub-thread for listening. (Worker)")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True)
    # Generate a new block.
    def generate_block(self):
        index = len(self.blockchain.blocks)
        # When a new block is generated, the basic info sent is
        # timestamp, transaction, and uuid of this worker.
        """ index, previous hash and hash are used after verification."""
        new_block = Block(index,
                          str(datetime.now()),
                          'Block_transaction',
                          self.blockchain.blocks[index-1].hash,
                          self.mac
                          )

        return new_block
            
    def process(self, str_json):
        "index, timestamp, transaction, previous_hash, mac"
        time = str_json['timestamp']
        transaction = str_json['transaction']
        mac = str_json['mac']
        data = {
                'timestamp': time,
                'transaction': transaction,
                'mac': mac
                }
        if len(str_json) == 5:
            if len(self.blockchain.blocks) == 0:
                preHash = str_json['previous_hash']
                print("This Worker receives Gensesis Block, Store it.")
                self.blockchain.add_blockG(time, transaction, preHash, mac)
            else:
                print("Gensesis Block is existing in worker, drop this Gensesis Block.")
        else:
            print("This Worker receives common block, save it into compare list.")
            self.compareList.append(data)
           # self.blockchain.add_block(time, transaction, mac) moved to other place.
    
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
    #host, port, mac, debug, IPs
    macStr = '00:11:22:33:44:' + sys.argv[1].split('.')[3] 
    
    w = Worker(sys.argv[1], sys.argv[2], macStr, False, sys.argv[4:])
    
   
    
    
    
