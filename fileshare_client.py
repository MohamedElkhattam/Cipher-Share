import hashlib
import os
import socket
import json
import crypto_utils


class FileShareClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.session_key = None
        self.shared_files = {}
        self.credentials_file = 'client_credentials.enc'
        self.client_side_HashedPassword = 'hashed_password.enc'
        # saved only client side

    def save_credentials(self, username, password, remember_me=False):
        if not remember_me:
            return

        hashed_password = crypto_utils.hash_password(password)
        salt = os.urandom(16)
        key = crypto_utils.derive_key_from_password(hashed_password, salt)

        credentials = {
            'username': username,
            'password': password
        }

        encrypted_data = crypto_utils.encrypt_files(
            json.dumps(credentials).encode(),
            key
        )

        with open(self.credentials_file, 'wb') as f:
            f.write(salt + encrypted_data)

        with open(self.client_side_HashedPassword, 'wb') as f:
            f.write(hashed_password.encode())

    def load_credentials(self):
        if not os.path.exists(self.credentials_file) and not os.path.exists(self.client_side_HashedPassword):
            return None, None

        try:
            with open(self.client_side_HashedPassword, 'rb') as f:
                hashed_password = f.read().decode()
            with open(self.credentials_file, 'rb') as f:
                data = f.read()

            # Extract salt and encrypted data
            salt = data[:16]
            encrypted_data = data[16:]

            try:
                key = crypto_utils.derive_key_from_password(
                    hashed_password, salt)
                decrypted_data = crypto_utils.decrypt_files(
                    encrypted_data, key)
                credentials = json.loads(decrypted_data)
                return credentials['username'], credentials['password']
            except Exception as e:
                print(f"[Client] Decryption failed: {e}")
                return None, None

        except Exception as e:
            print(f"[Client] Error loading credentials: {e}")
            return None, None

    def clear_credentials(self):
        if os.path.exists(self.credentials_file) and os.path.exists(self.client_side_HashedPassword):
            os.remove(self.credentials_file)
            os.remove(self.client_side_HashedPassword)

    def connect_to_peer(self, peer_address):
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(peer_address)
            print(f"[Client] Connected to peer at {peer_address}")
        except Exception as e:
            print(
                f"Exception connection to Peer Server with address{peer_address}:{e}")

    def authenticate_session(self):
        self.client_socket.send(self.session_key.encode())
        isAuth = self.client_socket.recv(1024).decode()
        return isAuth

    def register_user(self, username, password):
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

    def login_user(self, username, password, remember_me=False):
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
            if remember_me:
                self.save_credentials(username, password, True)
            return True

    def upload_file(self, filepath):
        try:
            self.client_socket.send('UPLOAD'.encode())
            if self.authenticate_session() == "INVALID_SESSION":
                print("[Client] Session Expired!")
                return False

            file_name = os.path.basename(filepath)
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

            file_id = crypto_utils.hash_sha256(file_data)
            self.shared_files[file_id] = file_name

            print(f"[Client] File Uploaded Successfully")
            return True
        except Exception as e:
            print(f"[Client] Upload failed: {e}")
            return False

    def download_file(self, filename, destination_path):
        try:
            self.client_socket.send('DOWNLOAD'.encode())
            if self.authenticate_session() == "INVALID_SESSION":
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

            file_size = int(self.client_socket.recv(1024).decode().strip())
            received_data = b''
            while len(received_data) < file_size:
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    break
                received_data += chunk

            # Decrypting File Data
            try:
                file_data = crypto_utils.decrypt_files(
                    received_data, AES_precise_encryption_key)
            except Exception as e:
                print(f"[Client] Decryption failed: {e}")
                return False

            # Save decrypted file
            try:
                full_path = os.path.join(destination_path, filename)
                with open(full_path, 'wb') as file:
                    file.write(file_data)

                print(
                    f"[Client] File '{filename}' saved to {destination_path}")

                return True
            except Exception as e:
                print(f"[Client] Failed to save file: {e}")
                return False

        except Exception as e:
            print(f"[Client] Download failed: {e}")
            return False

    def search_files(self, file_name):
        # ...Search for files in the P2P network using DHT...
        try:
            self.client_socket.send("SEARCH".encode())
            if self.authenticate_session() == "INVALID_SESSION":
                print("[Client] Session Expired!")
                return False

            self.client_socket.send(file_name.encode())
            response = json.loads(self.client_socket.recv(1024).decode())

            if response["status"] == "FILE_FOUND":
                file_info = response["file_info"]
                print("\n[Client] File Found!")
                print(f"File Name: {file_info['file_name']}")
                print(f"Owner: {file_info['owner']}")
                print(f"Size: {file_info['size']} bytes")
                return True
            else:
                print("\n[Client] File Not Found")
                return False
        except Exception as e:
            print(f"[Client] Search failed: {e}")
            return False

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
