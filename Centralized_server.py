import json
import socket
import threading


class CentralizedServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.online_peers = []

    def start_server(self):
        self.server_socket.bind(('localhost', 8080))
        self.server_socket.listen()
        print("Server Listening On Port 8080")
        while True:
            peer_connection, _ = self.server_socket.accept()
            server_thread = threading.Thread(target=self.handle_incoming_peers, args=(peer_connection,))
            server_thread.start()

    def handle_incoming_peers(self, peer_connection):
        try:
            peer_address = peer_connection.recv(1024).decode()
            self.online_peers.append(peer_address)
            while True:
                command = peer_connection.recv(1024).decode()
                if command == "ONLINE_PEERS":
                    online_peers_dict = {}
                    for i in range(len(self.online_peers)):
                        if self.online_peers[i] != peer_address:
                            online_peers_dict[i + 1] = self.online_peers[i]
                    peer_connection.send(json.dumps(online_peers_dict).encode())
        except Exception as e:
            print(e)


if __name__ == "__main__":
    server = CentralizedServer()
    server.start_server()
