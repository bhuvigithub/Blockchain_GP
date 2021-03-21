#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 13:38:44 2021

@author: mininet
"""

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
"GET"
while True:
    host = input()
    if host == 'exit':
    	exit(0)
    index = input()
    url = "https://10.0.0." + str(host) + ":5000/blockchains/" + str(index)
    print(url)
    index = 0
    result = ''
    for i in range(1, int(host)+1):
    	response = requests.get(url, verify=False)
    	if index == 0:
    		result = response.content
    		print(response.content)
    	else:
    		if result != response.content :
    			print("Block on Host" + str(i) + " is Wrong")
    	index + index + 1
    


