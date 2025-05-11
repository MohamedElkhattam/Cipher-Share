import hashlib
import os
import json
import uuid
import socket
import datetime
import threading
import time
import crypto_utils
from Distributed_hash_table import Node


class FileSharePeer:
    def __init__(self, port):
        self.port = int(port)
        self.host = '127.0.0.1'
        self.peer_socket = None
        self.connected_users = []
        self.client_socket = None
        self.authenticated_username = None
        self.shared_files = {}
        # {file_id: {'filename': str, 'owner': str, 'size': int, 'file_path': str}}
        self.dht_node = None

    def storeFileHash(self, file_name, file_path, file_size, owner=None):
        # ...Store file metadata in the DHT network...
        try:
            file_id = crypto_utils.getFileId(file_name.encode())
            # Store locally
            self.shared_files[file_id] = {
                'filename': file_name,
                'owner': owner or self.authenticated_username,
                'size': file_size,
                'file_path': file_path
            }

            if self.dht_node:
                self.dht_node.mySavedFiles[file_id] = {
                    'file_name': file_name,
                    'owner': owner or self.authenticated_username,
                    'size': file_size,
                    'file_id': file_id
                }

                #  Store in k-closest nodes
                k_closest_nodes = self.dht_node.get_kClosestNodes(file_id)
                print(
                    f"[Peer] Distributing file to {len(k_closest_nodes)} closest nodes")

                for node in k_closest_nodes:
                    response = self.dht_node.make_rpc_call(
                        node.socketAddress,
                        'store_file',
                        {'file_info': self.dht_node.mySavedFiles[file_id]}
                    )
                    if response and response.get('status') == 'OK':
                        print(
                            f"[Peer] Successfully stored file metadata at node {node.id}")
                    else:
                        print(
                            f"[Peer] Failed to store file metadata at node {node.id}")
            else:
                print("[Peer] DHT node not available for file storage")
        except Exception as e:
            print(f"[Peer] Error storing file in DHT: {e}")

    def lookUpFile(self, file_name):
        # ...Search for a file in the DHT network...
        try:
            if not self.dht_node:
                print("[Peer] DHT node not available for file lookup")
                return False, None

            file_id = crypto_utils.getFileId(file_name.encode())

            # First check local files
            if file_id in self.dht_node.mySavedFiles:
                print(f"[Peer] File found locally: {file_name}")
                return True, self.dht_node.mySavedFiles[file_id]

            # Then check DHT network
            print(f"[Peer] Searching DHT network for file: {file_name}")
            k_closest_nodes = self.dht_node.get_kClosestNodes(file_id)

            for node in k_closest_nodes:
                response = self.dht_node.make_rpc_call(
                    node.socketAddress,
                    'lookup_file',
                    {'file_id': file_id}
                )
                if response and response.get('status') == 'OK':
                    print(f"[Peer] File found at node {node.id}")
                    return True, response['file_info']
                elif response and response.get('status') == 'NOT_FOUND':
                    print(f"[Peer] File not found at node {node.id}")
                    continue

            print(f"[Peer] File not found in DHT network: {file_name}")
            return False, None
        except Exception as e:
            print(f"[Peer] Error looking up file: {e}")
            return False, None

    def start_peer(self):
        try:
            self.peer_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.peer_socket.bind((self.host, self.port))
            self.peer_socket.listen(5)
            print(f"[Peer] Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.peer_socket.accept()
                self.client_socket = client_socket
                self.connected_users.append(client_address)

                print(f"[Peer] Connected to {client_address}")
                client_thread = threading.Thread(
                    target=self.handle_client_connection, args=(client_address,))
                client_thread.start()

        except Exception as e:
            print(f"[Peer] Server error: {e}")
            if self.peer_socket:
                self.peer_socket = None
                self.peer_socket.close()

    def handle_client_connection(self, client_address):
        try:
            while True:
                command = self.client_socket.recv(1024).decode()

                # ..........REGISTER..........
                if command == "REGISTER":
                    username, hashed_pass = str(
                        self.client_socket.recv(1024).decode()).split("||")
                    jsonFile_data = json_file_read()

                    if username in jsonFile_data:
                        self.client_socket.send("USER_ALREADY_EXISTS".encode())
                        print("[Peer] User already exists!")
                    else:
                        user = {
                            "hashed_pass": hashed_pass,
                            "session_id": None,
                            "session_expiration_date": None,
                            "isOnline": False,
                        }
                        jsonFile_data[username] = user

                        with open('credentials.json', 'w') as json_file:
                            json.dump(jsonFile_data, json_file, indent=4)

                        self.client_socket.send("OK".encode())
                        print("[Peer] User Registered Successfully")

                # ..........Login..........
                elif command == "LOGIN":
                    username, password = str(
                        self.client_socket.recv(1024).decode()).split("||")
                    jsonFile_data = json_file_read()

                    if username in jsonFile_data:
                        res = crypto_utils.verify_password(
                            password, jsonFile_data[username]["hashed_pass"])

                        if res:
                            if jsonFile_data[username]["isOnline"] is True:
                                self.client_socket.send(
                                    "USER_LOGGED_IN".encode())
                            else:
                                session_id = str(uuid.uuid4())

                                jsonFile_data[username]["session_id"] = session_id
                                session_expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
                                jsonFile_data[username]["session_expiration_date"] = session_expiration_date.isoformat(
                                )
                                jsonFile_data[username]["isOnline"] = True

                                self.authenticated_username = username
                                with open('credentials.json', 'w') as json_file:
                                    json.dump(jsonFile_data,
                                              json_file, indent=4)

                                self.client_socket.send(session_id.encode())

                                # Initialize DHT node with the different port
                                self.dht_node = Node(
                                    (self.host, self.port))

                                print("[Peer] User logged in successfully")
                        else:
                            self.client_socket.send(
                                "WRONG_CREDENTIALS".encode())
                    else:
                        self.client_socket.send("WRONG_CREDENTIALS".encode())

                # ..........Upload..........
                elif command == "UPLOAD":
                    sessionId = str(self.client_socket.recv(1024).decode())
                    if not is_authenticated(sessionId):
                        self.client_socket.send("INVALID_SESSION".encode())
                        break
                    self.client_socket.send("AUTHENTICATED".encode())

                    # Receive File Name and check for its existence
                    file_name = self.client_socket.recv(1024).decode()
                    if file_name in self.shared_files.keys():
                        print(f"[Peer] file {file_name} already exists")
                        continue

                    # Key Exchange using Diffie-Hellman
                    peer2_private, peer2_public, P = crypto_utils.generate_key_pair()
                    self.client_socket.send(str(peer2_public).encode())
                    peer1_public = int(self.client_socket.recv(1024))
                    shared_key = pow(peer1_public, peer2_private, P)

                    # Receiving Encrypted File size and data
                    file_size = int(self.client_socket.recv(1024).decode())
                    received_data = b''
                    while len(received_data) < file_size:
                        chunk = self.client_socket.recv(4096)
                        if not chunk:
                            break
                        received_data += chunk

                    # Decrypting File Data
                    AES_precise_encryption_key = hashlib.sha256(
                        str(shared_key).encode()).digest()
                    file_data = crypto_utils.decrypt_files(
                        received_data, AES_precise_encryption_key)

                    # Save file locally
                    with open(f"{file_name}", 'wb') as file:
                        file.write(file_data)

                    # Store file metadata in DHT
                    full_path = os.path.join(os.getcwd(), file_name)
                    self.storeFileHash(
                        file_name, full_path, file_size, self.authenticated_username)
                    print(
                        f"[Peer] Received and stored file '{file_name}' successfully.")

                # ........Download........
                elif command == "DOWNLOAD":
                    sessionId = str(self.client_socket.recv(1024).decode())
                    if not is_authenticated(sessionId):
                        self.client_socket.send("INVALID_SESSION".encode())
                        break
                    self.client_socket.send("AUTHENTICATED".encode())

                    # Receiving file name and checking for its existence
                    filename = self.client_socket.recv(1024).decode()
                    file_id = crypto_utils.getFileId(filename.encode())
                    if file_id not in self.shared_files:
                        self.client_socket.send("FILE_NOT_FOUND".encode())
                        print("[Peer] File not found.")
                        continue

                    # Key Exchange using Diffie-Hellman
                    peer1_private, peer1_public, P = crypto_utils.generate_key_pair()
                    self.client_socket.send(str(peer1_public).encode())
                    peer2_public = int(self.client_socket.recv(1024))
                    shared_key = pow(peer2_public, peer1_private, P)
                    AES_precise_encryption_key = hashlib.sha256(
                        str(shared_key).encode()).digest()

                    # Preparing file path
                    file_path = self.shared_files[file_id]['file_path']

                    try:
                        # Read and encrypt file
                        with open(file_path, 'rb') as file:
                            file_data = file.read()
                        encrypted_data = crypto_utils.encrypt_files(
                            file_data, AES_precise_encryption_key)

                        # Send encrypted data size
                        size_message = str(len(encrypted_data)).encode()
                        self.client_socket.sendall(size_message)

                        # Send encrypted data
                        self.client_socket.sendall(encrypted_data)
                        time.sleep(0.01)


                        print(f"[Peer] File '{filename}' sent to client.")
                    except Exception as e:
                        print(f"[Peer] Error sending file: {e}")
                        continue

                # ..........Searching Files..........
                elif command == "SEARCH":
                    sessionId = str(self.client_socket.recv(1024).decode())
                    if not is_authenticated(sessionId):
                        self.client_socket.send("INVALID_SESSION".encode())
                        break
                    self.client_socket.send("AUTHENTICATED".encode())

                    file_name = self.client_socket.recv(1024).decode()
                    found, file_info = self.lookUpFile(file_name)

                    if found:
                        response = {
                            "status": "FILE_FOUND",
                            "file_info": file_info
                        }
                        self.client_socket.send(json.dumps(response).encode())
                        print(f"[Peer] File found: {file_name}")
                    else:
                        self.client_socket.send(json.dumps(
                            {"status": "FILE_NOT_FOUND"}).encode())
                        print(f"[Peer] File not found: {file_name}")

                # ..........Client Disconnected..........
                elif command == "DISCONNECT":
                    sessionId = str(self.client_socket.recv(1024).decode())
                    json_data = json_file_read()
                    for data in json_data.values():
                        if data["session_id"] == sessionId:
                            data["isOnline"] = False
                            with open('credentials.json', 'w') as json_file:
                                json.dump(json_data, json_file, indent=4)
                            break
                    self.connected_users.remove(client_address)
                    break

        except Exception as e:
            print(f"[Peer] Error handling client {client_address}: {e}")
            if self.client_socket:
                self.client_socket.close()
                self.cleanup()
            if client_address in self.connected_users:
                self.connected_users.remove(client_address)

    def cleanup(self):
        # ...Clean up resources when peer is shutting down...
        try:
            # Clean up DHT node
            if self.dht_node:
                self.dht_node.cleanup()
                print("[Peer] DHT node cleaned up")

            # Clean up peer socket
            if self.peer_socket:
                self.peer_socket.close()
                print("[Peer] Peer socket closed")

            if self.authenticated_username:
                json_data = json_file_read()
                if self.authenticated_username in json_data:
                    json_data[self.authenticated_username]["isOnline"] = False
                    with open('credentials.json', 'w') as json_file:
                        json.dump(json_data, json_file, indent=4)
                print("[Peer] User status updated")
        except Exception as e:
            print(f"[Peer] Error during cleanup: {e}")


def json_file_read():
    if os.path.getsize('credentials.json') > 0:
        with open('credentials.json', 'r') as json_file:
            parsed_json_data = json.load(json_file)
    else:
        parsed_json_data = {}
        with open('credentials.json', 'w') as json_file:
            json.dump(parsed_json_data, json_file, indent=4)
    return parsed_json_data


def is_authenticated(session_id):
    json_data = json_file_read()
    date_obj = datetime.datetime
    for data in json_data.values():
        if data['session_id'] == session_id:
            if date_obj.fromisoformat(data['session_expiration_date']) >= date_obj.now():
                return True
            else:
                data['isOnline'] = False
                with open('credentials.json', 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)
                return False
    return False
