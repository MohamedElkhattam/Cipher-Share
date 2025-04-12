import os
import socket


class FileShareClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.username = None
        # self.session_key = None

    def connect_to_peer(self, peer_address):
        try:
            self.client_socket.connect(peer_address)
            print(f"Connected to peer at {peer_address}")
            return True
        except Exception as e:
            print(f"Error connecting to peer {peer_address}: {e}")
            return False

    def register_user(self, username, password):
        # ... (Implement registration process -
        #  send username, hashed password + salt to a registration service / peer -
        #  how to distribute user info in P2P? - Simplification needed, perhaps a dedicate
        #  'user registry' peer initially or file-based for simplicity) ...
        # ... (Client-side password hashing and salt generation) ...
        pass

    def login_user(self, username, password):
        # ... (Implement login process -
        # send username, password - server/peer
        # authenticates against stored hashed password - handle session -
        # simplified session management for P2P could be token-based or direct connection based).
        # ... (Client-side password hashing to compare against stored hash) ...
        pass

    def upload_file(self, filepath):
        # ... (Read file in chunks, encrypt chunks, send chunks to peer -
        # need to implement P2P file transfer protocol - simplified) ...
        # ... (File encryption using crypto_utils, integrity hash generation) ...
        try:
            self.client_socket.send('UPLOAD'.encode())
            file_size = os.path.getsize(filepath)
            file_name = os.path.basename(filepath)
            with open(filepath, 'rb') as file:
                file_data = file.read()

            self.client_socket.send(file_name.encode())
            self.client_socket.send(str(file_size).encode())
            self.client_socket.sendall(file_data)
            print(f"File Uploaded Successfully to peer")

        except Exception as e:
            print(f"Client upload failed: {e}")
        finally:
            file.close()
            self.client_socket.close()

    def download_file(self, filename, destination_path):  # there should be fileId
        # ... (Request file from peer, receive encrypted chunks, decrypt chunks, verify integrity,
        # save file) ...
        # ... (File decryption, integrity verification) ...
        try:
            self.client_socket.send('DOWNLOAD'.encode())
            self.client_socket.send(filename.encode())

            file_size_data = self.client_socket.recv(1024).decode()
            if file_size_data == "FILE_NOT_FOUND":
                print(f"File '{filename}' not found on peer.")
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

            print(f"File '{filename}' saved to {destination_path}")

        except Exception as e:
            print(f"Download failed: {e}")

        finally:
            self.client_socket.close()
            file.close()

    def search_files(self, keyword):
        # ... (Implement file search in the P2P network - broadcasting?
        # Distributed Index? - Simplification required) ...
        pass

    def list_shared_files(self):
        # ... (Keep track of locally shared files and display them) ...
        # ... (Methods for P2P message handling, network discovery - simplified) ...
        # ... (Client program entry point, user interface loop) ...
        pass
