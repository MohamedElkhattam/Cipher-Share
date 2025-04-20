import os
import json
import uuid
import socket
import datetime
import threading
import crypto_utils


def json_file_read():
    if os.path.getsize('credentials.json') > 0:
        with open('credentials.json', 'r') as json_file:
            parsed_json_data = json.load(json_file)
    else:
        parsed_json_data = {"users": []}
        with open('credentials.json', 'w') as json_file:
            json.dump(parsed_json_data, json_file, indent=4)
    return parsed_json_data


# ... (Data structures for user info, shared files, peer lists etc.)...
class FileSharePeer:
    def __init__(self, port):
        self.peer_socket = None
        self.port = int(port)
        self.host = '127.0.0.1'
        self.connected_users = []
        self.shared_files = {}  # {file_name: [filepath , fileSize]}
        # {file_id: [filepath, owner_username, ...]} - Track files shared by this peer

    def start_peer(self):
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.bind((self.host, self.port))
        self.peer_socket.listen(5)
        print("[Peer] Server listening ...")

        while True:
            client_socket, client_address = self.peer_socket.accept()
            self.connected_users.append(client_address)
            print(f"[Peer] Connected to {client_address}")
            client_thread = threading.Thread(target=self.handle_client_connection,
                                             args=(client_socket, client_address))
            client_thread.start()

    def handle_client_connection(self, client_socket, client_address):
        try:
            while True:
                # ... (Receive commands from client - register, login, upload, download, search, etc. - define a simple protocol) ...
                # Example - define command structure
                command = str(client_socket.recv(1024).decode())

                # ...REGISTER...
                if command == "REGISTER":
                    username, hashed_pass = str(client_socket.recv(1024).decode()).split("||")
                    jsonFile_data = json_file_read()

                    for user in jsonFile_data["users"]:
                        if user["username"] == username:
                            client_socket.send("USER_ALREADY_EXISTS".encode())
                            print("[Peer] User already exists!")
                            break
                    else:
                        user = {
                            "username": username, "hashed_pass": hashed_pass,
                            "session_id": None, "session_expiration_date": None
                        }
                        jsonFile_data["users"].append(user)

                        with open('credentials.json', 'w') as json_file:
                            json.dump(jsonFile_data, json_file, indent=4)

                        client_socket.send("OK".encode())
                        print("[Peer] User Registered Successfully")

                # .......Login.........
                elif command == "LOGIN":
                    # No 2 users logged in with same credentials
                    username, password = str(client_socket.recv(1024).decode()).split("||")
                    jsonFile_data = json_file_read()
                    for user in jsonFile_data["users"]:
                        if user["username"] == username:
                            res = crypto_utils.verify_password(password, user["hashed_pass"])
                            if res:
                                session_id = str(uuid.uuid4())
                                user["session_id"] = session_id
                                session_expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
                                user["session_expiration_date"] = session_expiration_date.isoformat()
                                with open('credentials.json', 'w') as json_file:
                                    json.dump(jsonFile_data, json_file, indent=4)
                                client_socket.send(session_id.encode())
                                print("[Peer] User logged in  successfully")
                                break
                    else:
                        client_socket.send("WRONG_CREDENTIALS".encode())

                # ......Upload........
                elif command == "UPLOAD":
                    # ... (Receive file metadata, then encrypted file chunks, store chunks, update shared_files list) ...
                    file_name = client_socket.recv(1024).decode()
                    if file_name in self.shared_files.keys():
                        # client_socket.send("FILE_EXISTS".encode())
                        print(f"[Peer] file {file_name} already exists")
                        continue
                    file_size = int(client_socket.recv(1024).decode())
                    file_data = b''
                    while len(file_data) < file_size:
                        packet = client_socket.recv(file_size - len(file_data))
                        if not packet:
                            break
                        file_data += packet
                    with open(f"{file_name}", 'wb') as file:
                        file.write(file_data)
                    cwd = os.getcwd()
                    self.shared_files[file_name] = [cwd, file_size]
                    print(f"[Peer] Received file '{file_name}' successfully.")

                # ........Download........
                elif command == "DOWNLOAD":
                    # ... (Receive file ID, retrieve encrypted file chunks, send chunks to requesting client) ...
                    filename = client_socket.recv(1024).decode()
                    if filename not in self.shared_files.keys():
                        client_socket.send(str("FILE_NOT_FOUND").encode())
                        print("[Peer] File not found.")
                        continue

                    filepath = os.path.join(
                        self.shared_files[filename][0], filename)
                    file_size = self.shared_files[filename][1]
                    client_socket.send(str(file_size).encode())
                    try:
                        with open(filepath, 'rb') as file:
                            file_data = file.read()
                            client_socket.sendall(file_data)
                        print(f"[Peer] File '{filename}' sent to client.")
                    except Exception as e:
                        print(f"[Peer] Error sending file '{filename}': {e}")
                        client_socket.send("ERROR".encode())  # Indicate error
                    finally:
                        file.close()

                # Searching Files
                elif command == "SEARCH":
                    # ... (Receive search keyword, search local shared files, respond with file list - for simplified P2P search) ...
                    filename = client_socket.recv(1024).decode()
                    if filename in self.shared_files.keys():
                        client_socket.send(str("FILE_FOUND").encode())
                    else:
                        client_socket.send(str("FILE_NOT_FOUND").encode())

                # Client Disconnected
                elif command == "DISCONNECT":
                    self.connected_users.remove(client_address)
                    break
        except WindowsError:
            print(WindowsError)  # To be fixed

        except Exception as e:
            print(f"[Peer] Error handling client {client_address}: {e}")
