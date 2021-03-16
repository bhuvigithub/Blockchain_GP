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
"uuid can be used in extension 1. MAC address"
from uuid import uuid4
from WorkerData import WorkerData
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

class Miner:
    def __init__(self, host, port, debug, worker_nodes):
        # host: the host ip of Miner
        # port: port of Miner connection
        # debug: on/off debug mode
        # IPs: the ip addresses of workers
        self.host = host
        self.port = port
        self.debug = False
        self.worker_nodes = worker_nodes
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
            print("Receive block from: " + request.remote_addr)
            if not request.data:
                abort(400)
            str = request.data.decode('utf-8')
            str_json = json.loads(str)
            self.waitingList.append(str_json)
            return jsonify(str_json)
        
        #route that stores the public key of the workers
        @self.app.route('/key-receiver', methods=['POST'])
        def receive_public_key():
            ip_addr = request.remote_addr
            print("received key from:" + ip_addr)
            json_data = request.get_json()
            pub_key = RSA.import_key(json_data['pub_key'].encode('utf-8'))
            worker = self.get_worker(ip_addr) 
            if(worker == None):
                print("worker with IP " + ip_addr + " not found") 
                return jsonify({"error": "Worker not stored on the miner"}), 401
            else:
                index_of_worker = worker_nodes.index(worker)
                worker_nodes[index_of_worker].pub_key = pub_key
                return jsonify({"msg": "Key is updated"}), 201

        # Directly start the Miner.
        self.start()
        
    # start contains the main thread and a sub-thread. 
    # Main thread: always checking waiting list
    def start(self):
        
        # 1. Start sub-thread to listen workers for public key and block.
        subthread1 = threading.Thread(target = self.listen)
        subthread1.start()
        
        time.sleep(5)
        # 2. Send the Gensesis Block to all workers.
        self.sendGenBlock()
        
        time.sleep(3)
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
        for i in range(len(self.worker_nodes)):
            url = 'http://' + self.worker_nodes[i].ip + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data))
            if i == 0:
                print("Created Gensesis Block content:")
                print(response.content)   
                
    # Flask app start
    def listen(self):
        print("Start sub-thread for listening.")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True)
        
    # Process block
    def processBlock(self):
        print("Process one block:")
        signed_Block = self.waitingList[0]
        "verify may contain decyptions, drop block and others?"
        processedBlock = self.verify_block(signed_Block)
        # After verify successfully, broadcast block to all workers.
        if(processedBlock != None):
            self.broadcast(processedBlock)
        
    # Validates a block
    def verify_block(self, signed_block):
        del(self.waitingList[0]) #block is removed from the list in any case
        
        str_block = signed_block['block']
        json_block = json.loads(str_block.replace("'",'"'))
        mac = json_block['mac'] 
        signature = signed_block['signature']
        hash = SHA256.new(str_block.encode())
        pub_key = self.get_key(mac)
        "the pub_key needs to be compared using string, otherwise crash"
        if(str(pub_key) == "None"):
             print('No public key for given MAC address')
             return False

        try:
            pkcs1_15.new(pub_key).verify(hash,bytearray.fromhex(signature))
            print('block was successfully validated')
            self.blockchains.add_block(json_block['timestamp'], 
                                        json_block['transaction'],
                                        json_block['mac'])
            return json_block
        except(ValueError,TypeError): 
            print('block is not valid!')
            return None

    # Broadcast common block to all workers.
    def broadcast(self, block):
        print("Broadcast the block")
        "index, previous_hash are existing in all workers'ledger."
        "timestamp, transaction and mac, the three parameter are essential and basic."
        "if previous hash is in the broadcast data packet, maybe it is not safe."
        print(block)
        data = {
                # 'index': len(self.blockchains.blocks), deleted
                'timestamp': block['timestamp'],
                'transaction': block['transaction'],
                # 'previous_hash': self.blockchains.blocks[len(self.blockchains.blocks) - 1].previous_hash, deleted
                'mac': block['mac']
                }
        for i in range(len(self.worker_nodes)):
            url = 'http://' + self.worker_nodes[i].ip + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data))
            if i == 0:
                print("Broadcast Common Block content:")
                print(response.content)
    
    #helper function
    def get_key(self,mac):
        for worker in self.worker_nodes:
            if(worker.mac ==  mac):
                return worker.pub_key
        return None

    #helper function
    def get_worker(self,ip_addr):
        for worker in self.worker_nodes:
            if(worker.ip ==  ip_addr):
                return worker
        return None  

def createWorker(WorkerDataList):
    
     for i in (sys.argv[4:]):
        list = i.split('.')
        macStr = '00:11:22:33:44:0' + list[3]
        print(macStr)
        WorkD = WorkerData(i, macStr)
        WorkerDataList.append(WorkD)
        
if __name__ == '__main__': 
    # Test mode
    # Miner's ip is 10.0.0.1
    # All workers' port are 5000
    WorkerDataList =[]
    createWorker(WorkerDataList)
    print(sys.argv[1], sys.argv[2], sys.argv[3], WorkerDataList)
    miner = Miner(sys.argv[1], sys.argv[2], sys.argv[3], WorkerDataList)
    #miner = Miner('10.0.0.1', 5000, False, [WorkerData('10.0.0.2','00:11:22:33:44:02')])
