#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 13:38:44 2021

@author: mininet
"""

import requests
import json
"GET"
while True:
    host = input()
    index = input()
    url = "https://10.0.0." + str(host) + ":5000/blockchains/" + str(index)
    print(url)
    response = requests.get(url, verify=False)
    print(response.content)


