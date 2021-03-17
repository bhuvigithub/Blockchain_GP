#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 09:32:14 2021

@author: mininet
"""
#from Block import *
from Block import Block
from datetime import datetime
"uuid is for MAC address"
from uuid import uuid4
class Blockchain:
    def __init__(self, type):
        self.blocks = []
        if type == 'Miner':
            self.blocks = [self.get_genesis_block()]
        elif type == 'Worker':
            self.blocks = []
    
    def get_genesis_block(self):
        return Block(0, 
                     'Genesis_transaction',
                     'Genesis_transaction',
                     'Genesis_previousHash',
                     'Genesis_mac')
    def add_blockG(self, time, transaction, preHash, mac):
        #time = str(datetime.now())
        self.blocks.append(Block(len(self.blocks),
                                 time,
                                 transaction,
                                 preHash,
                                 mac
                                 ))
    """ When the blockchain add a block, the basic info contains
        timestamp, data and mac. The other info can be known from ledgers or
        calculation, like index, previous hash from the length of chain, the
        hash value from calculation.   
    """
    def add_block(self, time, transaction, mac):
        #time = str(datetime.now())
        self.blocks.append(Block(len(self.blocks),
                                 time,
                                 transaction,
                                 self.blocks[len(self.blocks) - 1].hash,
                                 mac
                                 ))
                  
        