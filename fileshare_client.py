import hashlib
import os
import socket
import crypto_utils


class FileShareClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.session_key = None
        self.shared_files = {}

    def connect_to_peer(self, peer_address):
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(peer_address)
            print(f"[Client] Connected to peer at {peer_address}")
        except Exception as e: #TODO : Needs exception to remove offline peers
            print(f"Exception connection to Peer Server with address{peer_address}:{e}")

    def authenticate_session(self):
        self.client_socket.send(self.session_key.encode())
        isAuth = self.client_socket.recv(1024).decode()
        return isAuth

    def register_user(self, username, password):
        #  how to distribute user info in P2P? - Simplification needed, perhaps a dedicate
        #  'user registry' peer initially or file-based for simplicity) ...
        # ... (Client-side password hashing and salt generation) ...
        if len(username) < 4 or len(password) < 4:
            print("[Client] Username or password is too short")
            return False
        self.client_socket.send("REGISTER".encode())
        hashed_password = crypto_utils.hash_password(password)
        self.client_socket.send(f"{username}||{hashed_password}".encode())
        res = self.client_socket.recv(1024).decode()
        if res == "OK":
            return True
        print("[Client] " + res)
        return False

    def login_user(self, username, password):
        # authenticates against stored hashed password - handle session -
        # simplified session management for P2P could be token-based or direct connection based).
        # ... (Client-side password hashing to compare against stored hash) ...
        if len(username) == 0 or len(password) == 0:
            print("[Client] Please enter username and password")
            return False

        self.client_socket.send("LOGIN".encode())
        self.client_socket.send(f"{username}||{password}".encode())
        res = self.client_socket.recv(1024).decode()
        if res == "WRONG_CREDENTIALS":
            print("[Client] " + res)
            return False
        elif res == "USER_LOGGED_IN":
            print("[Client] " + "User is already logged in")
            return False
        else:
            self.session_key = res
            self.username = username
            return True

    def upload_file(self, filepath):
        # ... (Read file in chunks, encrypt chunks, send chunks to peer -
        # need to implement P2P file transfer protocol - simplified) ...
        # ... (File encryption using crypto_utils, integrity hash generation) ...
        try:
            self.client_socket.send('UPLOAD'.encode())
            if self.authenticate_session() == "INVALID_SESSION":
                print("[Client] Session Expired!")
                return False

            file_name = os.path.basename(filepath)  # File name
            self.client_socket.send(file_name.encode())

            with open(filepath, 'rb') as file:
                file_data = file.read()

            # Key Exchange using Diffie-Hellman
            peer1_private, peer1_public, P = crypto_utils.generate_key_pair()
            self.client_socket.send(str(peer1_public).encode())
            peer2_public = int(self.client_socket.recv(1024))
            shared_key = pow(peer2_public, peer1_private, P)

            # File size
            file_size = os.path.getsize(filepath)
            self.client_socket.send(str(file_size).encode())

            # Encrypting File and sending it
            AES_precise_encryption_key = hashlib.sha256(
                str(shared_key).encode()).digest()
            encryptedFileBytes = crypto_utils.encrypt_files(
                file_data, AES_precise_encryption_key)
            self.client_socket.sendall(encryptedFileBytes)

            # Saving File_id as key and file name/s as value
            file_id = crypto_utils.hash_sha256(file_data)
            self.shared_files.setdefault(file_id, []).append(file_name)
            print(f"[Client] File Uploaded Successfully")
        except Exception as e:
            print(f"[Client] Client upload failed: {e}")

    # noinspection DuplicatedCode
    def download_file(self, filename, destination_path):  # there should be fileId
        # ... (Request file from peer, receive encrypted chunks, decrypt chunks, verify integrity,
        # save file) ...
        # ... (File decryption, integrity verification) ...
        try:
            self.client_socket.send('DOWNLOAD'.encode())
            if self.authenticate_session() == "INVALID_SESSION":
                print("[Client] Session Expired!")
                print("[Client] Session Expired!")
                return False
            self.client_socket.send(filename.encode())

            # Key Exchange using Diffie-Hellman
            peer2_private, peer2_public, P = crypto_utils.generate_key_pair()
            self.client_socket.send(str(peer2_public).encode())
            peer1_public = int(self.client_socket.recv(1024))
            shared_key = pow(peer1_public, peer2_private, P)
            AES_precise_encryption_key = hashlib.sha256(
                str(shared_key).encode()).digest()
            print(AES_precise_encryption_key)
            # File Size or Error
            file_size_data = self.client_socket.recv(1024).decode()
            if file_size_data == "FILE_NOT_FOUND":
                print(f"[Client]  File '{filename}' not found on peer.")
                return
            file_size = int(file_size_data)

            # Receiving Encrypted File Data
            received_data = b''
            while len(received_data) < file_size:
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    break
                received_data += chunk
            # Decrypting File Data
            file_data = crypto_utils.decrypt_files(
                received_data, AES_precise_encryption_key)
            full_path = os.path.join(destination_path, filename)
            with open(full_path, 'wb') as file:
                file.write(file_data)
            print(f"[Client] File '{filename}' saved to {destination_path}")
        except Exception as e:
            print(f"[Client] Download failed: {e}")

    def search_files(self, file_name):  # Keyword
        # ... (Implement file search in the P2P network - broadcasting?
        # Distributed Index? - Simplification required) ...

        self.client_socket.send("SEARCH".encode())
        print("Send function command")
        if self.authenticate_session() == "INVALID_SESSION":
            print("[Client] Session Expired!")
            return False

        self.client_socket.send(file_name.encode())
        res = self.client_socket.recv(1024).decode()
        if res == "FILE_FOUND":
            print("File Found")
            return
        print("File Not Found")
        return

    def list_shared_files(self):
        if not self.shared_files:
            return None
        else:
            return list(self.shared_files.values())

    def disconnect_peer(self):
        try:
            self.client_socket.send("DISCONNECT".encode())
            self.client_socket.send(self.session_key.encode())
            self.client_socket.close()
        except Exception:
            pass
