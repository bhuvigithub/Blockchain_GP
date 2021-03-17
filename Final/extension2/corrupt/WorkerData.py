#Class for worker objects that are stored in the list of the miner

class WorkerData():
    def __init__(self, ip, mac):
        self.ip = ip
        self.mac = mac
        self.pub_key = None