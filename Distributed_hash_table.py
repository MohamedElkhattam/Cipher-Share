import socket
import json
import threading
import time

K = 4
KEY_SPACE = 16
MAX_NODES_PER_BUCKET = 2

import crypto_utils


class Node:
    def __init__(self, socketAddress):
        self.socketAddress = tuple(socketAddress)
        self.id = None
        self.is_new_node = True
        self.buckets = [[] for _ in range(K)]
        self.mySavedFiles = {}
        # {file_id: {'file_name': str, 'owner': str, 'size': int}}
        self.rpc_server = None
        self.getNodeID(self.socketAddress)
        print(f"Node {self.id} created at {self.socketAddress}")
        self.start_rpc_server() if self.is_new_node else None

    def visualizeBuckets(self):
        print(f"\nNode {self.id} Buckets View")
        for i, bucket in enumerate(self.buckets):
            print(f"Bucket {i}: {[node.id for node in bucket]}")

    def start_rpc_server(self):
        try:
            rpc_address = (self.socketAddress[0], self.socketAddress[1] + 1)
            self.rpc_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rpc_server.bind(rpc_address)
            self.rpc_server.listen(5)
            print(f"[DHT] RPC server started at {rpc_address}")
            self.rpc_thread = threading.Thread(
                target=self.handle_rpc_requests, daemon=True)
            self.rpc_thread.start()
        except Exception as e:
            print(f"[DHT] Failed to start RPC server: {e}")
            self.rpc_server = None

    def getNodeID(self, nodeAddress):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 8080))
            client_socket.send("SET_NODE_ID".encode())
            time.sleep(0.01)
            client_socket.send(str(nodeAddress).encode())
            hasNode = client_socket.recv(1024).decode()
            if hasNode == "YES":
                node_id = client_socket.recv(1024).decode()
                self.id = int(node_id)
                self.is_new_node = False
            else:
                node_id = client_socket.recv(1024).decode()
                self.id = int(node_id)
                self.is_new_node = True
            client_socket.close()
        except Exception as e:
            print(f"[DHT] Error getting node ID: {e}")
            self.id = None

    def handle_rpc_requests(self):
        while self.rpc_server:
            try:
                client_socket, _ = self.rpc_server.accept()
                try:
                    request_data = client_socket.recv(1024).decode()
                    request = json.loads(request_data)

                    if request['method'] == 'store_node':
                        node_addr = tuple(request['params']['node_address'])
                        temp_node = Node(node_addr)
                        self.storeNode(temp_node)
                        print(
                            f"[DHT] Stored node {temp_node.id} at {self.id}")
                        response = {'status': 'OK'}

                    elif request['method'] == 'get_k_closest':
                        file_id = request['params']['file_id']
                        nodes = self.get_kClosestNodes(file_id)
                        response = {
                            'status': 'OK',
                            'nodes': [(node.id, node.socketAddress) for node in nodes]
                        }

                    elif request['method'] == 'store_file':
                        file_info = request['params']['file_info']
                        self.mySavedFiles[file_info['file_id']] = file_info
                        response = {'status': 'OK'}

                    elif request['method'] == 'lookup_file':
                        file_id = request['params']['file_id']
                        if file_id in self.mySavedFiles:
                            response = {
                                'status': 'OK',
                                'file_info': self.mySavedFiles[file_id]
                            }
                        else:
                            response = {'status': 'NOT_FOUND'}

                    else:
                        response = {'status': 'ERROR',
                                    'message': 'Unknown method'}
                    client_socket.send(json.dumps(response).encode())

                except json.JSONDecodeError:
                    print("[DHT] Invalid JSON received")
                except Exception as e:
                    print(f"[DHT] Error processing request: {e}")
                finally:
                    try:
                        client_socket.close()
                    except:
                        pass

            except Exception as e:
                print(f"[DHT] RPC Error: {e}")

    def make_rpc_call(self, target_address, method, params):
        try:
            rpc_address = (target_address[0], target_address[1] + 1)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(rpc_address)

                request = {
                    'method': method,
                    'params': params
                }
                s.send(json.dumps(request).encode())
                response_data = s.recv(1024)
                if not response_data:
                    raise Exception("No response received")

                response = json.loads(response_data.decode())
                return response
        except Exception as e:
            print(f"[DHT] RPC call failed to {target_address}: {e}")
            return None

    def storeNode(self, node):
        if node.id == self.id:
            return

        bucket_index = (self.id ^ node.id).bit_length() - 1
        bucket = self.buckets[bucket_index]

        if len(bucket) < MAX_NODES_PER_BUCKET:
            # Check if node already exists in bucket
            for existing_node in bucket:
                if existing_node.socketAddress == node.socketAddress:
                    return

            bucket.append(node)
            print(f"Node {node.id} Stored at Node {self.id}")

            # Notify other nodes in the bucket about the new node
            for existing_node in bucket:
                if existing_node != node:
                    response = self.make_rpc_call(
                        existing_node.socketAddress,
                        'store_node',
                        {'node_address': node.socketAddress}
                    )
                    if response and response.get('status') == 'OK':
                        print(
                            f"[DHT] Successfully notified node {existing_node.id} about new node {node.id}")
                    else:
                        print(
                            f"[DHT] Failed to notify node {existing_node.id} about new node {node.id}")
        else:
            print(f"[Bucket Full] Node {self.id}'s Bucket {bucket_index} full")
            xorMinimum = float('inf')
            closestNode = None

            for i in range(MAX_NODES_PER_BUCKET):
                xor_distance = bucket[i].id ^ node.id
                if xor_distance < xorMinimum:
                    xorMinimum = xor_distance
                    closestNode = bucket[i]

            if closestNode:
                response = self.make_rpc_call(
                    closestNode.socketAddress,
                    'store_node',
                    {'node_address': node.socketAddress}
                )
                if response and response.get('status') == 'OK':
                    print(
                        f"[DHT] Successfully forwarded node {node.id} to closest node {closestNode.id}")
                else:
                    print(
                        f"[DHT] Failed to forward node {node.id} to closest node {closestNode.id}")

    def get_kClosestNodes(self, fileId, visited=None):
        if visited is None:
            visited = set()

        visited.add(self)
        nodeDistanceList = []

        # Gather all known nodes from buckets
        for bucket in self.buckets:
            for node in bucket:
                if node not in visited:
                    distance = fileId ^ node.id
                    nodeDistanceList.append((distance, node))

        nodeDistanceList.sort(key=lambda x: x[0])  # Xor distance sorting

        # Add all current candidates to the set, ensuring no duplicate IDs
        allCandidates = {}
        for _, node in nodeDistanceList:
            if node.id not in allCandidates:
                allCandidates[node.id] = node

        # Query each candidate using RPC
        for _, node in nodeDistanceList:
            if node not in visited:
                response = self.make_rpc_call(
                    node.socketAddress,
                    'get_k_closest',
                    {'file_id': fileId}
                )
                if response and 'nodes' in response:
                    for node_id, node_addr in response['nodes']:
                        if node_id not in visited and node_id not in allCandidates:
                            new_node = Node(tuple(node_addr))
                            allCandidates[node_id] = new_node

        sorted_nodes = sorted(allCandidates.values(),
                              key=lambda node: fileId ^ node.id)
        print("List of kClosestNodes is ", sorted_nodes)
        return sorted_nodes[:K - 1]

    def storeFileHash(self, fileName, owner=None, fileSize=None):
        # ...Store file in the DHT network using RPC...
        fileId = crypto_utils.getFileId(fileName.encode())

        file_info = {
            'file_name': fileName,
            'owner': owner or str(self.socketAddress),
            'size': fileSize,
            'file_id': fileId
        }

        self.mySavedFiles[fileId] = file_info

        kClosestNodes = self.get_kClosestNodes(fileId)
        for node in kClosestNodes:
            self.make_rpc_call(
                node.socketAddress,
                'store_file',
                {'file_info': file_info}
            )

    def lookUpFile(self, fileName):
        # ...Look up file in the DHT network using RPC...
        fileId = crypto_utils.getFileId(fileName.encode())

        if fileId in self.mySavedFiles:
            return True, self.mySavedFiles[fileId]

        kClosestNodes = self.get_kClosestNodes(fileId)
        for node in kClosestNodes:
            response = self.make_rpc_call(
                node.socketAddress,
                'lookup_file',
                {'file_id': fileId}
            )
            if response and response.get('status') == 'OK':
                return True, response['file_info']

        return False, None

    def cleanup(self):
        try:
            # Notify the server about node removal
            try:
                client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(('localhost', 8080))
                client_socket.send("REMOVE_NODE".encode())
                client_socket.close()
            except Exception as e:
                print(f"[DHT] Error notifying server during cleanup: {e}")

            if self.rpc_server:
                try:
                    self.rpc_server.close()
                except Exception as e:
                    print(f"[DHT] Error closing RPC server: {e}")
                finally:
                    self.rpc_server = None

        except Exception as e:
            print(f"[DHT] Error during cleanup: {e}")
