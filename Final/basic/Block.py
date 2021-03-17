#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 09:14:21 2021

@author: mininet
"""

import hashlib
class Block:
    def __init__(self, index, timestamp, transaction, previous_hash, mac):
        self.index = index
        self.timestamp = timestamp
        "transaction can be use in extension 2. It is a list."
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.mac = mac
        self.hash = self.hashing()
    
    def hashing(self):
        key = hashlib.sha256()
        key.update(str(self.index).encode('utf-8'))
        key.update(str(self.timestamp).encode('utf-8'))
        key.update(str(self.transaction).encode('utf-8'))
        key.update(str(self.previous_hash).encode('utf-8'))
        return key.hexdigest()
