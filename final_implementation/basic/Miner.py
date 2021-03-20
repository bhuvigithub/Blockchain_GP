#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 10:57:10 2021

@author: mininet
"""
from flask import Flask,jsonify,abort,request
import json
import threading
import requests
import time
from Blockchain import Blockchain
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#key_path='/home/mininet/Blockchain_GP/final_implementation/encryption/host'
#cert_path='/home/mininet/Blockchain_GP/final_implementation/encryption/host'
#Test for dynamic encryption pickup
key_path='../encryption/host'
cert_path='../encryption/host'
class Miner:
    def __init__(self, host, port, debug, IPs):
        # host: the host ip of Miner
        # port: port of Miner connection
        # debug: on/off debug mode
        # IPs: the ip addresses of workers
        self.host = host
        self.port = port
        self.debug = False
        self.IPs = IPs
        self.ID = int(self.host.split('.')[3])
        # blockchains: the blockchain of Miner. its type is Miner, 
        # which contains Gensesis Block.
        self.blockchains = Blockchain('Miner')
        # Waiting list of miner, all received blocks are stored in it in order.
        self.waitingList = []
        # Flask app creation
        self.app = Flask(__name__)
        # Flask app method1: View the blockchain on miner by index.
        @self.app.route('/blockchains/<int:id>',methods=['GET'])
        def get_blockchains(id):
            data = {
                    'index': self.blockchains.blocks[id].index,
                    'timestamp': self.blockchains.blocks[id].timestamp,
                    'transaction': self.blockchains.blocks[id].transaction,
                    'previous_hash': self.blockchains.blocks[id].previous_hash,
                    'mac': self.blockchains.blocks[id].mac,
                    'hash': self.blockchains.blocks[id].hash
                    }
            return jsonify(data)
           
        # Flask app method2: Receiver of Miner, receive block from workers
        # After receiving block, it adds the block to Waiting list directly.
        @self.app.route('/minerReceiver', methods=['POST'])
        def receive_block():
            print("Receive block from: " )
            if not request.data:
                abort(400)
            str = request.data.decode('utf-8')
            str_json = json.loads(str)
            self.waitingList.append(str_json)
            return jsonify(str_json)
        
        # Directly start the Miner.
        self.start()
        
    # start contains the main thread and a sub-thread. 
    # Main thread: always checking waiting list
    def start(self):
        "Set a timeout fro waiting all workers to start."
        time.sleep(10)
        # 1. Send the Gensesis Block to all workers.
        self.sendGenBlock()
        # 2. Start sub-thread to listen workers.
        subthread1 = threading.Thread(target = self.listen)
        subthread1.start()
        # 3. Main thread always check waiting list.
        while True:
            print("Main thread is checking waitling list.")
            if len(self.waitingList) > 0:
                print("Waiting list length > 0, Miner verifies a block.")
                self.processBlock()
            time.sleep(4)
            
    # Send the genesis block created by Miner to all workers.
    def sendGenBlock(self):
        "Gensesis Block content"
        data = {
                'index': self.blockchains.blocks[0].index,
                'timestamp': self.blockchains.blocks[0].timestamp,
                'transaction': self.blockchains.blocks[0].transaction,
                'previous_hash': self.blockchains.blocks[0].previous_hash,
                'mac': self.blockchains.blocks[0].mac
                }
        #  Send to all workers
        for i in range(len(self.IPs)):
            url = 'https://' + self.IPs[i] + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data), verify=False)
            if i == 0:
                print("Created Gensesis Block content:")
                print(response.content)   
                
    # Flask app start
    def listen(self):
        print("Start sub-thread for listening.")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True,
                     ssl_context=(cert_path + str(self.ID)+"/cert.pem",key_path+ str(self.ID)+ "/key.pem"))
        
    # Process block
    def processBlock(self):
        print("Process one block:")
        processedBlock = self.waitingList[0]
        "verify may contain decyptions, drop block and others?"
        self.verify_block(processedBlock)
        # After verify successfully, broadcast block to all workers.
        self.broadcast(processedBlock)
        
    # Verify block.
    "ubfinished, add decyption"
    " Thomas's part"
    def verify_block(self, block):
        print("Verify the block successfully.")
        # After successful verify, add the block to blockchain.
        " can add more decyption at there."
        self.blockchains.add_block(block['timestamp'], 
                                   block['transaction'],
                                   block['mac'])
        """
        ELGamal or RSA and its result.
        """
        del(self.waitingList[0])
        "can add a result of verify and return it"
    # Broadcast common block to all workers.
    def broadcast(self, block):
        print("Broadcast the block")
        "index, previous_hash are existing in all workers'ledger."
        "timestamp, transaction and mac, the three parameter are essential and basic."
        "if previous hash is in the broadcast data packet, maybe it is not safe."
        data = {
                # 'index': len(self.blockchains.blocks), deleted
                'timestamp': block['timestamp'],
                'transaction': block['transaction'],
                # 'previous_hash': self.blockchains.blocks[len(self.blockchains.blocks) - 1].previous_hash, deleted
                'mac': block['mac']
                }
        for i in range(len(self.IPs)):
            url = 'https://' + self.IPs[i] + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data), verify=False)
            if i == 0:
                print("Broadcast Common Block content:")
                print(response.content)  
        
if __name__ == '__main__': 
    # Test mode
    # Miner's ip is 10.0.0.1
    # All workers' port are 5000
    
    #miner = Miner('10.0.0.1', 5000, False, ['10.0.0.2','10.0.0.3', '10.0.0.4','10.0.0.5', '10.0.0.6'])
    #miner = Miner('10.0.0.1', 5000, False, ['10.0.0.2'])
    # Combination mode
    "When we combine Starter.py, it can set the parameter."
    #print(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    miner = Miner(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    # h1.cmd(MinerIP, MinerPort, MinerDebugMode, WorkerIPList)
    

