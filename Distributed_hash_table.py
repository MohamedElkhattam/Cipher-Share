import hashlib

K = 4
KEY_SPACE = 16
MAX_NODES_PER_BUCKET = 2
GLOBAL_NODES_DICT = {}


def getFileId(key):
    hash_bytes = hashlib.sha1(key).digest()
    return int.from_bytes(hash_bytes, 'big') % 16


class Node:
    def __init__(self, socketAddress):
        self.socketAddress = socketAddress
        self.buckets = [[] for _ in range(K)]
        self.id = self.calculate_hash(socketAddress)
        print(f"Node Created with ID {self.id} for {self.socketAddress}")
        self.mySavedFiles = {}
        # {file_name: [filepath , fileSize]}
        # {file_id: [[file_names], filepath, owner_username, fileSize]} Needed

    def visualizeBuckets(self):
        print(f"\nNode{self.id} Buckets View")
        for innerList in self.buckets:
            print([i.id for i in innerList], end=" ")
        print()

    def calculate_hash(self, node):
        hash_bytes = hashlib.sha1(node.encode()).digest()
        id_4bit = int.from_bytes(hash_bytes, 'big') % 16
        while id_4bit in GLOBAL_NODES_DICT.keys():
            node += "_"
            hash_bytes = hashlib.sha1(node.encode()).digest()
            id_4bit = int.from_bytes(hash_bytes, 'big') % 16
        GLOBAL_NODES_DICT[id_4bit] = self
        return id_4bit

    def storeNode(self, node):
        if node.id == self.id:
            return
        bucket_index = (self.id ^ node.id).bit_length() - 1
        if len(self.buckets[bucket_index]) < MAX_NODES_PER_BUCKET:
            GLOBAL_NODES_DICT[node.id] = node
            self.buckets[bucket_index].append(node)
        else:
            print(f"Bucket {bucket_index} reached it's Max capacity!")
            xorMinimum = float('inf')
            closestNode = None
            for i in range(MAX_NODES_PER_BUCKET):
                xor_distance = self.buckets[bucket_index][i].id ^ node.id
                if xor_distance < xorMinimum:
                    xorMinimum = xor_distance
                    closestNode = self.buckets[bucket_index][i]
            closestNode.storeNode(node)

    def lookupNode(self, node):
        if node.id == self.id:
            return
        bucket_index = (self.id ^ node.id).bit_length() - 1
        if node in self.buckets[bucket_index]:
            return self
        else:
            xorMinimum = float('inf')
            closestNode = None
            for currNode in self.buckets[bucket_index]:
                xor_distance = currNode.id ^ node.id
                if xor_distance < xorMinimum:
                    xorMinimum = xor_distance
                    closestNode = currNode
            if closestNode:
                return closestNode.lookupNode(node)
            else:
                return None

    def lookupFile(self, file):
        fileId = getFileId(file)
        if fileId in self.mySavedFiles.keys():
            return [self]
        nodesWithDistances = []

        for bucket in self.buckets:
            for currNode in bucket:
                distance = currNode.id ^ fileId
                nodesWithDistances.append((distance, currNode))

        # Sorting based on XORMetric
        nodesWithDistances.sort(key=lambda x: x[0])
        closest_nodeIds = nodesWithDistances[0:K-1]
        resultNodes = [node for _, node in closest_nodeIds]
        print(resultNodes)
        for node in resultNodes:
            print(node.id)
        '''
        This will be returned inside the search command
        '''

    # def storeFileHash(self, file):
    #     self.lookupFile(file)


# (15, 14, 3) k Closest
node1 = Node('(127.0.0.1,1500)')  # ID -> 5
node2 = Node('(127.0.0.1,9000)')  # ID -> 15
node3 = Node('(127.0.0.1,6500)')  # ID -> 4
node4 = Node('(127.0.0.1,8500)')  # ID -> 14
node5 = Node('(127.0.0.1,2000)')  # ID -> 3
node6 = Node('(127.0.0.1,4000)')  # ID -> 6

# (15, 14, 1) k Closest
node7 = Node('(127.0.0.1,1234)')   # ID -> 9
node8 = Node('(127.0.0.1,0989)')   # ID -> 1
node9 = Node('(127.0.0.1,9090)')
# ID -> 8 # Not in node1 but do one hop from node1 to node4
node10 = Node('(127.0.0.1,0970)')  # ID -> 7

with open(r"C:\Users\medo2\Pictures\Saved Pictures\Screenshot 2022-08-26 213824.png", 'rb') as file:
    file_data = file.read()


node1.storeNode(node2)
node1.storeNode(node3)
node1.storeNode(node4)
node1.storeNode(node5)
node1.storeNode(node6)
node1.storeNode(node8)
node1.storeNode(node9)
node1.storeNode(node10)
node1.visualizeBuckets()

node7.storeNode(node8)
node7.storeNode(node9)
node7.storeNode(node10)
node7.visualizeBuckets()

node = node1.lookupNode(node9)
if node:
    print("Node stored at node with ID =", node.id)
else:
    print("Node Not found")
