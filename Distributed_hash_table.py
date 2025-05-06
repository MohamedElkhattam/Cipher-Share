import hashlib

K = 4
KEY_SPACE = 16
MAX_NODES_PER_BUCKET = 2
GLOBAL_NODES_DICTIONARY = {}


def getFileId(key):
    hash_bytes = hashlib.sha1(key).digest()
    return int.from_bytes(hash_bytes, 'big') % 16


class Node:
    def __init__(self, socketAddress):
        self.socketAddress = socketAddress
        self.mySavedFiles = {}
        self.buckets = [[] for i in range(K)]
        self.id = self.calculate_hash(socketAddress)
        print("Node Created with ID =", self.id)

    def calculate_hash(self, node):
        hash_bytes = hashlib.sha1(node.encode()).digest()
        id_4bit = int.from_bytes(hash_bytes, 'big') % 16
        while id_4bit in GLOBAL_NODES_DICTIONARY.keys():
            node += "_"
            hash_bytes = hashlib.sha1(node.encode()).digest()
            id_4bit = int.from_bytes(hash_bytes, 'big') % 16
        GLOBAL_NODES_DICTIONARY[id_4bit] = node
        return id_4bit

    def store_Node(self, node):
        if node.id == self.id:
            return
        bucket_index = (self.id ^ node.id).bit_length() - 1
        if len(self.buckets[bucket_index]) < MAX_NODES_PER_BUCKET:
            GLOBAL_NODES_DICTIONARY[node.id] = node.socketAddress
            self.buckets[bucket_index].append(node)

    def lookupFile(self, fileId):
        closetNode = None
        smallerNodeId = float('inf')
        for bucket in (self.buckets):
            for currNode in bucket:
                xorMetric = currNode.id ^ fileId
                if xorMetric < smallerNodeId:
                    smallerNodeId = xorMetric
                    closetNode = currNode
        return smallerNodeId, closetNode.id

    def readFile(self, file):
        self.lookupFile(file)

    def storeFileHash(self, file):
        self.lookupFile(file)


node1 = Node('(127.0.0.1,1500)')
node2 = Node('(127.0.0.1,9000)')
node3 = Node('(127.0.0.1,6500)')
node4 = Node('(127.0.0.1,8500)')
node5 = Node('(127.0.0.1,2000)')
node6 = Node('(127.0.0.1,4000)')

with open("D:\Coding\Python_Projects\shared_files\image.png", 'rb') as file:
    file_data = file.read()

fileID = getFileId(file_data)

node1.store_Node(node2)
node1.store_Node(node3)
node1.store_Node(node4)
node1.store_Node(node5)
node1.store_Node(node6)

print(fileID)
print(node1.lookupFile(fileID))
# print(node15.buckets)
