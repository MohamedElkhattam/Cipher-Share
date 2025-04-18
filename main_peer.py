import json
import os
import socket
import threading
from fileshare_client import FileShareClient as Client
from fileshare_peer import FileSharePeer as Peer


class PeerMain:
    def __init__(self, peer_server_port):
        self.port = peer_server_port
        self.client = None
        self.peer = None

    def run_server(self):
        self.peer = Peer(self.port)
        threading.Thread(target=self.peer.start_peer, daemon=True).start()
        # Runs Server concurrently with main Thread

    def run_client(self, peer_address):
        self.client = Client()
        threading.Thread(target=self.client.connect_to_peer, args=(peer_address,)).start()
        # Runs Client concurrently with main Thread


if __name__ == "__main__":
    peerMain = None
    connected = False
    centralizedServer_socket = None
    try:


        portNumber = int(input("Enter the port number: "))
        peerMain = PeerMain(portNumber)
        peerMain.run_server()

        # Connecting to Centralized Server
        centralizedServer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        centralizedServer_socket.connect(('localhost', 8080))
        print("[Peer] Connected to Centralized server")

        while True:
            centralizedServer_socket.sendall(f"{peerMain.peer.host},{peerMain.peer.port}".encode())
            see_peers = input("List Online Peers ? (y/n):")
            if see_peers != "y":
                print("[Peer] Waiting for incoming requests")
                print("[Peer] Press Enter to connect to peer")
                while True:
                    click = input()
                    break
                continue
            centralizedServer_socket.send("ONLINE_PEERS".encode())
            data = centralizedServer_socket.recv(1024).decode()
            online_peers = json.loads(data)

            if online_peers == {}:
                print("[Peer] No online peers available")
                print("[Peer] Press Enter to check for online peers")
                while True:
                    click = input()
                    break
                continue
            else:
                while True:
                    print("List of Online Peers:\n" +
                          "\n".join([f"{peer_no}. Peer{str(peer_no)}" for peer_no in online_peers.keys()]))
                    print("Which peer you want to connect to ?")
                    peer_number = input()
                    if peer_number in online_peers.keys():
                        ip, port = str(online_peers[peer_number]).split(',')
                        print(f"Peer{peer_number} info -> IP = {ip} , Port = {port}")
                        menu_options = input(f"1. Connect to Peer{peer_number}\n2. List Online Peers\n3. Exit\n")
                        if menu_options == '1':
                            peerMain.run_client((ip, int(port))) #
                            connected = True
                            break
                        elif menu_options == '2':
                            continue
                        elif menu_options == '3':
                            break
                    else:
                        print("Wrong Input Try another input")

            while True and connected:
                userChoice = input("1. REGISTER\n2. LOGIN\n3. UPLOAD\n4. DOWNLOAD\n"
                                   "5. SEARCH\n6. Show All files\n7. Disconnect\n")

                # Authentication Section
                if userChoice == "1":
                    username = input("Please enter your username and password\nUsername :")
                    password = input("Password :")
                    peerMain.client.register_user(username, password)
                    # peerMain.handle_client('REGISTER' , username , password)
                elif userChoice == "2":
                    username = input("Please enter your username and password\nUsername :")
                    password = input("Password :")
                    peerMain.client.login_user(username, password)

                # File Handling Section
                elif userChoice == "3":
                    path = input("Please enter path of the file to be uploaded\nPath :")
                    if os.path.exists(path):
                        try:
                            peerMain.client.upload_file(path)
                        except Exception as e:
                            print(f"Upload file failed :{e}")
                    else:
                        print(f"File not found in :{path}")
                elif userChoice == "4":
                    filename = input("Please enter name of the file to be downloaded\nFilename: ")
                    path = input("Where you want to save your file\nPath :")
                    peerMain.client.download_file(filename, path)

                elif userChoice == "5":
                    filename = input("Please enter file name\nFilename: ")
                    isFound = peerMain.client.search_files(filename)
                    if isFound:
                        downloadOption = input("Want to download File? (y/n): \n")
                        if downloadOption.lower() == 'y':
                            destination_path = input("Please enter destination path\nDestination Path :")
                            peerMain.client.download_file(filename, destination_path)
                        else:
                            print("Returning to main menu...")
                    else:
                        print("The File you are searching for not found")

                elif userChoice == "6":
                    peerMain.client.list_shared_files()

                # Exit and wrong commands
                elif userChoice == "7":
                    peerMain.client.disconnect_peer()
                    print("Disconnected")
                    break
                else:
                    print("INVALID OPTION\n")

    except KeyboardInterrupt:
        print("Exiting...")

    except Exception as e:
        print(e)

    finally:
        print("Closing connection")
        if peerMain:
            for connection in peerMain.peer.connected_users:
                connection.close()
        centralizedServer_socket.close()
