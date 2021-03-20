Now, can use starter run blockchain directly:
# argv[1] means number of miner, argv[2] means number of workers.
# it will create 7 hosts, the last one run View.py
# just can change argv[2]
sudo python3 Starter.py 1 5

View.py
It is in while loop, each time input 2 number,
eg: 1 2--- 1 means 10.0.0.1, 2 means second block on its blockchain
    2 3--- 2 means 10.0.0.2, 3 means thrid block on its blockchain
    
After exit, run 'sudo mn -c' to clear mininet trash
