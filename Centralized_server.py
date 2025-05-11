import hashlib
import json
import socket
import threading
import time
from Distributed_hash_table import KEY_SPACE


class CentralizedServer:
    def __init__(self):
        self.server_socket = None
        self.online_peers = []
        self.DHT_nodes = {}

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 8080))
        self.server_socket.listen()
        print("[Server] Listening on port 8080")
        while True:
            peer_connection, _ = self.server_socket.accept()
            server_thread = threading.Thread(
                target=self.handle_incoming_peers, args=(peer_connection,))
            server_thread.start()

    def handle_incoming_peers(self, peer_connection):
        try:
            peer_address = None
            nodeAddress = None

            while True:
                command = peer_connection.recv(1024).decode()
                if command == "REGISTER_PEER":
                    peer_address = peer_connection.recv(1024).decode()
                    self.online_peers.append(peer_address)
                    print("[Server] Registered peer with address", peer_address)

                elif command == "ONLINE_PEERS":
                    online_peers_dict = {}
                    for i in range(len(self.online_peers)):
                        if self.online_peers[i] != peer_address:
                            online_peers_dict[i + 1] = self.online_peers[i]
                    peer_connection.send(json.dumps(
                        online_peers_dict).encode())

                elif command == "DISCONNECT":
                    self.online_peers.remove(peer_address)
                    print(f"[Server] {peer_address} disconnected.")
                    break

                elif command == "SET_NODE_ID":
                    nodeAddress = peer_connection.recv(1024).decode()
                    if nodeAddress in self.DHT_nodes.values():
                        nodeID = [
                            id for id, address in self.DHT_nodes.items() if address == nodeAddress]
                        peer_connection.send("YES".encode())
                        time.sleep(0.01)
                        peer_connection.send(str(nodeID[0]).encode())
                    else:
                        peer_connection.send("NO".encode())
                        nodeID = self.getNodeID(nodeAddress)
                        peer_connection.send(str(nodeID).encode())

                elif command == "REMOVE_NODE":
                    print(f"[Server] Removing node with address {nodeAddress}")
                    if nodeAddress in self.DHT_nodes.values():
                        nodeID = [
                            id for id, address in self.DHT_nodes.items() if address == nodeAddress]
                        self.DHT_nodes.pop(nodeID[0])

        except Exception as e:
            print(e)

    def getNodeID(self, nodeAddress):
        n = 0
        while True:
            salted = f"{nodeAddress}_{n}"
            hash_bytes = hashlib.sha1(salted.encode()).digest()
            id_4bit = int.from_bytes(hash_bytes, 'big') % KEY_SPACE
            if id_4bit not in self.DHT_nodes.keys():
                self.DHT_nodes[id_4bit] = nodeAddress
                return id_4bit
            n += 1


if __name__ == "__main__":
    server = CentralizedServer()
    server.start_server()
