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
from WorkerData import WorkerData
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#key_path='/home/mininet/Blockchain_GP/final_implementation/encryption/host'
#cert_path='/home/mininet/Blockchain_GP/final_implementation/encryption/host'
#Dynamic encryption pickup
key_path='../../encryption/host'
cert_path='../../encryption/host'
class Miner:
    def __init__(self, host, port, debug, minersSize, minerIPs, worker_nodes ):
        # host: the host ip of Miner
        # port: port of Miner connection
        # debug: on/off debug mode
        # IPs: the ip addresses of workers
        self.host = host
        self.port = port
        self.debug = False
        self.minersSize = minersSize
        self.worker_nodes = worker_nodes
        # blockchains: the blockchain of Miner. its type is Miner, 
        # which contains Gensesis Block.
        self.blockchains = Blockchain('Miner')
        # Waiting list of miner, all received blocks are stored in it in order.
        self.waitingList = []
        # use it to compare results from other miners
        self.compareList = []
        self.ID = int(self.host.split('.')[3])
        self.minerIPList = minerIPs
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
        # receive public key from workers.
        @self.app.route('/verify-receiver', methods=['POST'])
        def verify_miner():
            # other miner ip address
            ip_addr = request.remote_addr
            print("received block from Miner:" + ip_addr)
            #json_data = request.get_json()
            str = request.data.decode('utf-8')
            str_json = json.loads(str)
            data = {
                'ip': ip_addr, 
                'timestamp': str_json['timestamp'],
                'transaction': str_json['transaction'],
                'mac': str_json['mac']
                }
            self.compareList.append(data)
            return jsonify(str_json)
        # Directly start the Miner.
        #
        print(self.minersSize)
        print(self.minerIPList)
        self.minerIPList.remove(str(self.host))
        self.start()
        
    # start contains the main thread and a sub-thread. 
    # Main thread: always checking waiting list
    def start(self):
        
        # 1. Start sub-thread to listen workers for public key and block.
        # Firstly, listen to all workers for their publick key.
        subthread1 = threading.Thread(target = self.listen)
        subthread1.start()
        
        time.sleep(15)
        # 2. Send the Gensesis Block to all workers.
        self.sendGenBlock()
        
        time.sleep(3)
        # 3. Main thread always check waiting list.
        while True:
            print("Main thread is checking waitling list.")
            if len(self.waitingList) > 0:
                print("Waiting list length > 0, Miner verifies a block.")
                self.processBlock()
            time.sleep(15)
            
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
            url = 'https://' + self.worker_nodes[i].ip + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data), verify=False)
            if i == 0:
                print("Created Gensesis Block content:")
                print(response.content)   
                
    # Flask app start
    def listen(self):
        print("Start sub-thread for listening.")
        print("CERT" + cert_path + str(self.ID)+"/cert.pem")
        print("KEY" + key_path+ str(self.ID)+ "/key.pem")
        self.app.run(self.host,
                     self.port,
                     self.debug,
                     threaded = True,
                     ssl_context=(cert_path + str(self.ID)+"/cert.pem",key_path+ str(self.ID)+ "/key.pem"))

        
    # Process block
    def processBlock(self):
        print("Process one block:")
        signed_Block = self.waitingList[0]
        "verify may contain decyptions, drop block and others?"
        
        processedBlock = self.verify_block(signed_Block)
        self.broadcastMiners(processedBlock)
        # After verify successfully, broadcast block to all workers.

        if(processedBlock != None):
            ## add a check at there
            while True:
                time.sleep(1)
                print("Checking compareList for miners:")
                if len(self.compareList) == int(self.minersSize):
                
                    processedBlock = self.verify_miners(processedBlock)
                    self.blockchains.add_block(processedBlock['timestamp'], 
                                        processedBlock['transaction'],
                                        processedBlock['mac'])
                    self.broadcast(processedBlock)
                    break
                
    def verify_miners(self, processedBlock):

        l = []
        for i in self.compareList: 
            compare_format = {
                    'timestamp': i['timestamp'],
                    'transaction': i['transaction'],
                    'mac': i['mac']
                    }
            l.append(compare_format)
       
        maxResult = (max(l, key = l.count))
        print("Correct Block in Miner check:" + str(maxResult))
        for i in range(len(l)):
            if l[i] == maxResult:
                print("Miner on " + str(self.compareList[i]['ip']) + " is correct.")
            else:
                print("Miner on " + str(self.compareList[i]['ip']) + " is corrupt.")
        self.compareList.clear()
        return maxResult
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
                    #value = 0
            itself = {
                    'ip': self.host, 
                    'timestamp': json_block['timestamp'],
                    'transaction': json_block['transaction'],
                    'mac': json_block['mac']                
                    }
            self.compareList.append(itself)
            print('block was successfully validated')
            #################
            """
            self.blockchains.add_block(json_block['timestamp'], 
                                        json_block['transaction'],
                                        json_block['mac'])
            self.broadcastMiners(json_block)
            """
            return json_block
        except(ValueError,TypeError): 
            print('block is not valid!')
            return None

    # Broadcast common block to all workers.
    def broadcast(self, block):
        print("Broadcast the block")
        #print(block)
        data = {
                # 'index': len(self.blockchains.blocks), deleted
                'timestamp': block['timestamp'],
                'transaction': block['transaction'],
                # 'previous_hash': self.blockchains.blocks[len(self.blockchains.blocks) - 1].previous_hash, deleted
                'mac': block['mac']
                }
        for i in range(len(self.worker_nodes)):
            url = 'https://' + self.worker_nodes[i].ip + ':5000/workerReceiver'
            response = requests.post(url , data = json.dumps(data), verify=False)
            if i == 0:
                print("Broadcast Common Block content:")
                print(response.content)
    def broadcastMiners(self, block):
        print("Broadcast the block to other miners")
        
        data = {
                'timestamp': block['timestamp'],
                'transaction': block['transaction'],
                'mac': block['mac']
                }
        
        ipList = self.minerIPList

        response =  ''
        print(ipList)
        for ip in ipList:
            url = 'https://' + ip + ':5000/verify-receiver'
            response = requests.post(url , data = json.dumps(data), verify=False)
        print(response)
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
     number_of_workers = int(sys.argv[4])
     worker_list = sys.argv[5+number_of_workers:]
     for i in worker_list:
        list = i.split('.')
        print(list)
        if int(list[3]) < 10:
            macStr = '00:11:22:33:44:0' + list[3]
        else:
            macStr = '00:11:22:33:44:' + list[3]
        
        print(macStr)
        WorkD = WorkerData(i, macStr)
        WorkerDataList.append(WorkD)

if __name__ == '__main__': 
    # Test mode
    # Miner's ip is 10.0.0.1
    # All workers' port are 5000
    
    host = sys.argv[1]
    port = sys.argv[2]
    debug = False
    minersSize = sys.argv[4]
    minerIPs = sys.argv[5:5+int(minersSize)]
    WorkerDataList =[]
    createWorker(WorkerDataList)
    
    print(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], "Miners:" + str(sys.argv[5:5+int(sys.argv[4])]) ,"Workers:"+str(sys.argv[5+int(sys.argv[4]):]))
    
    miner = Miner(host, port, debug, minersSize, minerIPs, WorkerDataList )
    #miner = Miner(sys.argv[1], sys.argv[2], False, sys.argv[4], WorkerDataList, ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4','10.0.0.5'])
    #(self, host, port, debug, minersSize, minerIPs, worker_nodes )
