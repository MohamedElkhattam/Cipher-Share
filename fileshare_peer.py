import socket
import threading
import os
import crypto_utils


# ... (Data structures for user info, shared files, peer lists etc.)...
class FileSharePeer:
    def __init__(self, port):
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = int(port)
        self.host = '127.0.0.1'
        self.connected_users = []
        self.users = {}  # {username: {hashed_password, salt, ...}} -In - memory for simplicity, consider file-based storage for persistence
        # {file_id: [filepath, owner_username, ...]} - Track files shared by this peer
        self.shared_files = {}  # {file_name: [filepath , fileSize]}

    def start_peer(self):
        self.peer_socket.bind((self.host, self.port))
        self.peer_socket.listen(5)
        print("[Peer] Server listening ...")

        while True:
            client_socket, client_address = self.peer_socket.accept()
            self.connected_users.append(client_socket)
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

                # .......Register........
                if command == "REGISTER":
                    # ... (store user info) ...
                    username, hashed_pass = str(
                        client_socket.recv(1024).decode()).split("||")
                    if username in self.users.keys():
                        client_socket.send("USER_ALREADY_EXISTS".encode())
                        print("[Peer]User already exists!")
                    else:
                        self.users[username] = hashed_pass
                        client_socket.send("REGISTER".encode())
                        print("[Peer] User stored successfully")

                # .......Login.........
                elif command == "LOGIN":
                    # ... (create session - simplified) ...
                    # Session + no 2 users logged in with same credentials
                    username, password = str(
                        client_socket.recv(1024).decode()).split("||")
                    if username in self.users.keys():
                        res = crypto_utils.verify_password(
                            password, self.users[username])
                        if res:
                            client_socket.send("OK".encode())
                            print("[Peer] User logged in  successfully")
                        else:
                            client_socket.send("INCORRECT_PASSWORD".encode())
                    else:
                        client_socket.send("USERNAME_NOT_FOUND".encode())

                # ......Upload........
                elif command == "UPLOAD":
                    # ... (Receive file metadata, then encrypted file chunks, store chunks, update shared_files list) ...
                    file_name = client_socket.recv(1024).decode()
                    if file_name in self.shared_files.keys():
                        print(f"[Peer] file {file_name} already exists")

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
                    return

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

                elif command == "LIST_FILES":
                    files_string = '$'.join(self.shared_files.keys())
                    client_socket.send(files_string.encode())
                    print(f"[Peer]{self.shared_files.keys()}")
        except WindowsError:
            pass  # To be fixed

        except Exception as e:
            print(f"[Peer] Error handling client {client_address}: {e}")

        finally:
            for conn in self.connected_users:
                self.connected_users.remove(conn)
            client_socket.close()
