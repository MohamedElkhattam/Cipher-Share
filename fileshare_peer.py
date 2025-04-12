import socket
import threading
import os


# ... (Data structures for user info, shared files, peer lists etc.)...
class FileSharePeer:
    def __init__(self, port):
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = int(port)
        self.host = 'localhost'
        self.users = {}  # {username: {hashed_password, salt, ...}} -In - memory for simplicity, consider file-based storage for persistence
        self.shared_files = {}  # {file_id: {filepath, owner_username, ...}} - Track files shared by this peer
        # {file_name: {filepath}}

    def start_peer(self):
        self.peer_socket.bind((self.host, self.port))
        self.peer_socket.listen(5)
        print(f"Peer listening on port {self.port}")

        while True:
            client_socket, client_address = self.peer_socket.accept()
            client_thread = threading.Thread(target=self.handle_client_connection,
                                             args=(client_socket, client_address))
            client_thread.start()

    def handle_client_connection(self, client_socket, client_address):
        print(f"Accepted connection from {client_address}")
        try:
            while True:
                # ... (Receive commands from client - register, login, upload, download, search, etc. - define a simple protocol) ...
                command = str(client_socket.recv(1024).decode())  # Example - define command structure
                if command == "REGISTER":
                    # ... (Handle user registration - receive username, hashed password + salt, store user info) ...
                    pass
                elif command == "LOGIN":
                    # ... (Handle login - receive username, password,verify password against stored hash, create session - simplified) ...
                    pass
                elif command == "UPLOAD":
                    # ... (Receive file metadata, then encrypted file chunks, store chunks, update shared_files list) ...
                    print("Uploading file accepted ...")
                    file_name = client_socket.recv(1024).decode()
                    if file_name in self.shared_files.keys():
                        print(f"Shared file {file_name} already exists")
                        return

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
                    print(f"Received file '{file_name}' '{file_size}' successfully.")
                    return

                elif command == "DOWNLOAD":
                    # ... (Receive file ID, retrieve encrypted file chunks, send chunks to requesting client) ...
                    filename = client_socket.recv(1024).decode()
                    if filename not in self.shared_files.keys():
                        client_socket.send(str("FILE_NOT_FOUND").encode())
                        return

                    filepath = os.path.join(self.shared_files[filename][0], filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        client_socket.send(str(file_size).encode())
                        with open(filepath, 'rb') as file:
                            file_data = file.read()
                            client_socket.sendall(file_data)
                        print(f"File '{filename}' sent to client.")
                        return

                    except Exception as e:
                        print(f"Error sending file '{filename}': {e}")
                        client_socket.send("ERROR".encode())  # Indicate error

                    finally:
                        file.close()

                elif command == "SEARCH":
                    # ... (Receive search keyword, search local shared files, respond with file list - for simplified P2P search) ...
                    pass
                # ... (Handle other commands) ...
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
        # ... (Methods for user registration, login, file upload, download, search, P2P network functions) ...
        # ... (Peer program entry point - start the peer node) ...
