#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 08:25:34 2021

@author: mininet
"""

"""Custom topology example

Two directly connected switches plus a host for each switch:

#
create topo with 1 worker and 1 miner
"""
import sys
import os
from time import sleep
from mininet.log import info,error
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.term import makeTerms
from flask import Flask,jsonify,abort,request
TOPOS = { 'testtopo': ( lambda: MyTopo() ) }
net = Mininet()
class MyTopo( Topo ):
    "create topo with 1 worker and 1 miner"
    def build( self, hostNum):
        c0=net.addController()
        s1=self.addSwitch('s1')
        for h in range(hostNum):
#            set host ip and MAC address
            host = self.addHost('h%s' % (h + 1),ip='10.0.0.%s' % (h + 1),mac='00:11:22:33:44:%s' % (h+1))
            "can add some network setting"
            # link = self.addLink(host,s1,delay='10ms',loss=30)
            link = self.addLink(host,s1)
            print(host)

def test(workerNum, minerNum, port, debugMode):
    hostNum = workerNum + minerNum + 1
    topo= MyTopo(hostNum)
    net = Mininet(topo=topo)
    net.start()
#    test connectivitiy between nodes
    dumpNodeConnections(net.hosts) 
    """t = 1      
    print(net.get('h1').cmd("xterm -title h%s -hold -e 'python3 Miner.py' &"%(t)))
    print(net.get('h2').cmd("xterm -title h2 -hold -e 'python3 Worker.py' &"))
    print(net.get('h3').cmd("xterm -title view -hold -e 'python3 View.py' &"))"""
    hostNum = workerNum + minerNum + 1
    workersIPs = []
    minersIPs = []
    index = 1
    for h in net.hosts:
        if index <= minerNum :
            minersIPs.append(h.IP())
        elif  minerNum < index < hostNum:
            workersIPs.append(h.IP())
        index = index + 1
    print("Miners' addresses:")
    print(minersIPs)
    print("Workers' addresses:")
    print(workersIPs)
    
    for h in net.hosts:
        
        name = h.name
        ip = h.IP()
        #minersIPs = str(minersIPs)
        #workersIPs = str(workersIPs)
        index = h.name.split('h')[1]
        if int(index) <= minerNum:                              
                 #     0               1            2                   3                  4                   [5:5+len(workerIPs)]   [9:]
            #5:5+len(workerIPs) 
            
            #   5  6  7 8
            " 10.0.04 10.0.05 10.0.0.6 10.0.07"
            #python3 Miner.py" + " "  + ip + " " + str(port) + " " + debugMode + " " +str(minerNum)+" " + str(' '.join(workersIPs)) + " " 
            
            command = "xterm -title " + name + " -hold -e 'python3 Miner.py" + " "  + ip + " " + str(port) + " " + debugMode + " " +str(minerNum) +" " + str(' '.join(workersIPs)) + " " + str(' '.join(minersIPs))+ "' &"
            print(command)
            print(net.get('h%s'%(index)).cmd(command))
            
        elif minerNum < int(index) < hostNum:
            command = "xterm -title " + name +" -hold -e 'python3 Worker.py" + " " + ip + " " + str(port) + " " + debugMode +  " "+ str(' '.join(minersIPs)) + "' &"
            print(command)
            print(net.get('h%s'%(index)).cmd(command))
        else:
            
            print(net.get('h%s'%(index)).cmd("xterm -title view -hold -e 'python3 View.py' &"))
    
    CLI(net)
    net.stopXterms()
if __name__=='__main__':
    setLogLevel('info')
    
    # total of miners
    minerNum = int(sys.argv[1])
    # total of workers
    workerNum = int(sys.argv[2])
    port = 5000
    debugMode = "False"
    test(workerNum, minerNum, port, debugMode)
    
    
    #print(net.get('%s'%(name)).cmd("xterm -title %s -hold -e 'python3 Miner.py %s %s %s %s' &" %(name, ip, port, debugMode, workersIPs)))
     #print(net.get('%s'%(name)).cmd("xterm -title %s -hold -e 'python3 Worker.py %s %s %s %s' &" %(name, ip, port, debugMode, minersIPs)))
            
