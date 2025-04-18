import os
import socket
import crypto_utils


class FileShareClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        # self.session_key = None

    def connect_to_peer(self, peer_address):
        # while True:
        try:
            self.client_socket.connect(peer_address)
            print(f"[Client]Connected to peer at {peer_address}")
            return
        # except ConnectionRefusedError:
        #     print("[Peer Client] No peers available, retrying in 5 seconds...")
        #     time.sleep(5)
        except Exception as e:
            print(f"Exception connection to Peer Server with address{peer_address}:{e}")
            # break

    def register_user(self, username, password):
        #  how to distribute user info in P2P? - Simplification needed, perhaps a dedicate
        #  'user registry' peer initially or file-based for simplicity) ...
        # ... (Client-side password hashing and salt generation) ...
        self.client_socket.send("REGISTER".encode())
        hashed_password = crypto_utils.hash_password(password)
        self.client_socket.send(f"{username}||{hashed_password}".encode())
        res = self.client_socket.recv(1024).decode()
        print("[Client]" + res)

    def login_user(self, username, password):
        # authenticates against stored hashed password - handle session -
        # simplified session management for P2P could be token-based or direct connection based).
        # ... (Client-side password hashing to compare against stored hash) ...
        self.client_socket.send("LOGIN".encode())
        self.client_socket.send(f"{username}||{password}".encode())
        res = self.client_socket.recv(1024).decode()
        if res == "OK":
            self.username = username
        print("[Client]" + res)

    def upload_file(self, filepath):
        # ... (Read file in chunks, encrypt chunks, send chunks to peer -
        # need to implement P2P file transfer protocol - simplified) ...
        # ... (File encryption using crypto_utils, integrity hash generation) ...
        try:
            self.client_socket.send('UPLOAD'.encode())
            file_name = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            with open(filepath, 'rb') as file:
                file_data = file.read()

            self.client_socket.send(file_name.encode())
            self.client_socket.send(str(file_size).encode())
            self.client_socket.sendall(file_data)
            print(f"[Client] File Uploaded Successfully to peer")
            file.close()
        except Exception as e:
            print(f"[Client] Client upload failed: {e}")

    def download_file(self, filename, destination_path):  # there should be fileId
        # ... (Request file from peer, receive encrypted chunks, decrypt chunks, verify integrity,
        # save file) ...
        # ... (File decryption, integrity verification) ...
        try:
            self.client_socket.send('DOWNLOAD'.encode())
            self.client_socket.send(filename.encode())

            file_size_data = self.client_socket.recv(1024).decode()
            if file_size_data == "FILE_NOT_FOUND":
                print(f"[Client]  File '{filename}' not found on peer.")
                return

            file_size = int(file_size_data)
            file_data = b''
            while len(file_data) < file_size:
                packet = self.client_socket.recv(file_size - len(file_data))
                if not packet:
                    break
                file_data += packet

            full_path = os.path.join(destination_path, filename)
            with open(full_path, 'wb') as file:
                file.write(file_data)

            print(f"[Client] File '{filename}' saved to {destination_path}")
            file.close()

        except Exception as e:
            print(f"[Client] Download failed: {e}")

    def search_files(self, file_name):  # Keyword
        # ... (Implement file search in the P2P network - broadcasting?
        # Distributed Index? - Simplification required) ...
        self.client_socket.send("SEARCH".encode())
        self.client_socket.send(file_name.encode())
        res = self.client_socket.recv(1024).decode()
        if res == "FILE_FOUND":
            return True
        return False

    def list_shared_files(self):
        # ... (Keep track of locally shared files and display them) ...
        # ... (Methods for P2P message handling, network discovery - simplified) ...
        self.client_socket.send("LIST_FILES".encode())
        files_string = self.client_socket.recv(1024).decode()
        if files_string == '{}':
            print("No shared files found.")
        else:
            for file_name in files_string.split('$'):
                print(file_name)
        # Please display all files you have

    def disconnect_peer(self):
        self.client_socket.close()
