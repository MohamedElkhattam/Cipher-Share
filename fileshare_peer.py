import hashlib
import os
import json
import uuid
import socket
import datetime
import threading
import crypto_utils
import re

# ... (Data structures for user info, shared files, peer lists etc.)...
# noinspection DuplicatedCode


class FileSharePeer:
    def __init__(self, port):
        self.port = int(port)
        self.host = '127.0.0.1'
        self.peer_socket = None
        self.connected_users = []
        self.client_socket = None
        self.authenticated_username = None
        self.shared_files = {}
        # TODO : Add new node

    def start_peer(self):
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.bind((self.host, self.port))
        self.peer_socket.listen(5)
        print("[Peer] Server listening ...")

        while True:
            client_socket, client_address = self.peer_socket.accept()
            self.client_socket = client_socket
            self.connected_users.append(client_address)
            print(f"[Peer] Connected to {client_address}")
            client_thread = threading.Thread(target=self.handle_client_connection,
                                             args=(client_address,))
            client_thread.start()

    def handle_client_connection(self, client_address):
        try:
            while True:
                command = self.client_socket.recv(1024).decode()

                # ...REGISTER...
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
                            "session_id": None, "session_expiration_date": None, "isOnline": False,
                        }
                        jsonFile_data[username] = user

                        with open('credentials.json', 'w') as json_file:
                            json.dump(jsonFile_data, json_file, indent=4)

                        self.client_socket.send("OK".encode())
                        print("[Peer] User Registered Successfully")

                # .......Login.........
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
                                print("[Peer] User logged in  successfully")
                        else:
                            self.client_socket.send(
                                "WRONG_CREDENTIALS".encode())
                    else:
                        self.client_socket.send("WRONG_CREDENTIALS".encode())

                # ......Upload........
                elif command == "UPLOAD":

                    sessionId = str(self.client_socket.recv(1024).decode())
                    result = is_authenticated(sessionId)
                    if not result:
                        self.client_socket.send("INVALID_SESSION".encode())
                        break
                    self.client_socket.send("AUTHENTICATED".encode())

                    # Receive File Name and check for it's existence
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
                    with open(f"{file_name}", 'wb') as file:
                        file.write(file_data)

                    # # Check for file id
                    # file_id = self.check_file_integrity(file)
                    # if not file_id:
                    #     self.client_socket.send("FILE_INTEGRITY_FAILED".encode())
                    # else:
                    #     # self.shared_files.setdefault(file_id, []).append(file_name)
                    cwd = os.getcwd()
                    self.shared_files[file_name] = [cwd, file_size]
                    print(self.shared_files)
                    print(f"[Peer] Received file '{file_name}' successfully.")

                # ........Download........
                elif command == "DOWNLOAD":

                    sessionId = str(self.client_socket.recv(1024).decode())
                    if not is_authenticated(sessionId):
                        self.client_socket.send("INVALID_SESSION".encode())
                        break
                    self.client_socket.send("AUTHENTICATED".encode())

                    # Receiving file nameChecking for file name existences
                    filename = self.client_socket.recv(1024).decode()
                    if filename not in self.shared_files.keys():
                        self.client_socket.send("FILE_NOT_FOUND".encode())
                        print("[Peer] File not found.")
                        continue

                    # Key Exchange using Diffie-Hellman
                    peer1_private, peer1_public, P = crypto_utils.generate_key_pair()
                    self.client_socket.send(str(peer1_public).encode())
                    peer2_public = int(self.client_socket.recv(1024))
                    shared_key = pow(peer2_public, peer1_private, P)
                    AES_precise_encryption_key_ = hashlib.sha256(
                        str(shared_key).encode()).digest()

                    # Preparing file path , file size
                    file_path = os.path.join(
                        self.shared_files[filename][0], filename)
                    file_size = self.shared_files[filename][1]
                    self.client_socket.send(str(file_size).encode())

                    # Encrypting file and sending it
                    with open(file_path, 'rb') as file:
                        file_data = file.read()
                    encrypt_file_data = crypto_utils.encrypt_files(
                        file_data, AES_precise_encryption_key_)
                    self.client_socket.sendall(encrypt_file_data)

                    print(f"[Peer] File '{filename}' sent to client.")

                # Searching Files
                elif command == r"SEARCH*":
                    # Client
                    if command == "SEARCH":
                        sessionId = str(self.client_socket.recv(1024).decode())
                        if not is_authenticated(sessionId):
                            self.client_socket.send("INVALID_SESSION".encode())
                            break
                        self.client_socket.send("AUTHENTICATED".encode())

                        file_name = self.client_socket.recv(1024).decode()
                        # if file_name in self.shared_files.keys():
                        #     self.client_socket.send("FILE_FOUND".encode())
                        # else:
                        #     self.client_socket.send("FILE_NOT_FOUND".encode())

                        # ? Replaced with Node Searching

                    # Node
                    else:
                        pass

                # Client Disconnected
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

        except WindowsError:
            print(WindowsError)  # To be fixed

        except Exception as e:
            print(f"[Peer] Error handling client {client_address}: {e}")

    # def check_file_integrity(self, file_content):
    #     file_id = crypto_utils.hash_sha256(file_content)
    #     hashed_file_Content = self.client_socket.recv(1024).decode()
    #     if hashed_file_Content == file_content:
    #         return file_id
    #     else:
    #         return False


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
