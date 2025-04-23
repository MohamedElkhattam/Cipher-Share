import json
import os
import socket
import threading
from InquirerPy import inquirer
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
    isLoggedIn = False
    connectedToPeer = False
    centralizedServer_socket = None
    try:
        portNumber = input("Enter the port number: ")
        peerMain = PeerMain(portNumber)
        peerMain.run_server()

        # Connecting to Centralized Server
        centralizedServer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        centralizedServer_socket.connect(('localhost', 8080))
        centralizedServer_socket.sendall(f"{peerMain.peer.host},{peerMain.peer.port}".encode())
        print("[Peer] Connected to Centralized server")

        while True:
            see_peers = inquirer.select(
                message="List Online Peers ?",
                choices=['Yes', 'No']).execute()
            if see_peers != 'Yes':
                print("Press Enter to connect to peer")
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
                    peer_number = inquirer.select(
                        message="List of Online Peers :",
                        choices=[
                            f"{peer_no}. Peer{str(peer_no)}" for peer_no in online_peers.keys()],
                    ).execute()[0]
                    ip, port = str(online_peers[peer_number]).split(',')
                    menu_options = inquirer.select(
                        message=f"Peer {peer_number} IP = {ip} , Port = {port}",
                        choices=[
                            f"1. Connect to Peer {peer_number}",
                            f"2. List Online Peers", "3. Exit"]).execute()[0]
                    if menu_options == '1':
                        peerMain.run_client((ip, int(port)))
                        connectedToPeer = True
                        break
                    elif menu_options == '2':
                        continue
                    elif menu_options == '3':
                        break

            while connectedToPeer and not isLoggedIn:
                # ...Authentication Section...
                AuthenticationChoice = inquirer.select(
                    message="Choose an Authentication :",
                    choices=["1. REGISTER", "2. LOGIN"]).execute()[0]

                if AuthenticationChoice == "1":
                    username = input("Username :")
                    password = input("Password :")
                    result = peerMain.client.register_user(username, password)
                    if result:
                        print("Registered Successfully Please login")
                        AuthenticationChoice = "2"
                if AuthenticationChoice == "2":
                    username = input("Username :")
                    password = input("Password :")
                    result = peerMain.client.login_user(username, password)
                    if result:
                        print("Logged In Successfully")
                        isLoggedIn = True

            while isLoggedIn and connectedToPeer:
                # ...File Handling Section...
                userChoice = inquirer.select(
                    message="Application Menu",
                    choices=["1. UPLOAD", "2. DOWNLOAD", "3. SEARCH", "4. Show All files", "5. Disconnect"]
                ).execute()[0]

                # ...File Upload...
                if userChoice == "1":
                    path = input("Please enter path of the file to be uploaded\nPath :")
                    if os.path.exists(path):
                        try:
                            result = peerMain.client.upload_file(path)
                            if result == False:
                                isLoggedIn = False
                                connectedToPeer = False
                                print("Session Invalid please login")
                                break
                        except Exception as e:
                            print(f"Upload file failed :{e}")
                    else:
                        print(f"File not found in :{path}")

                # ...File Download...
                elif userChoice == "2":
                    filename = input("Please enter file name\nFilename :")
                    destination_path = input("Where to download the file\nDestination Path :")
                    result = peerMain.client.download_file(filename, destination_path)
                    if result is False:
                        isLoggedIn = False
                        connectedToPeer = False
                        print("Session Invalid please login")
                        break
                    elif result is None:
                        print("File not found")

                # ...Search File...
                elif userChoice == "3":
                    filename = input("Please enter file name\nFilename :")
                    isFound = peerMain.client.search_files(filename)
                    if isFound:
                        downloadOption = inquirer.select(
                            message="Want to download File",
                            choices=['Yes', 'No']).execute()
                        if downloadOption == 'Yes':
                            destination_path = input("Where to download file\nDestination Path :")
                            peerMain.client.download_file(filename, destination_path)
                    else:
                        print("File not found")

                # ...List All Files...
                elif userChoice == "4":
                    result = peerMain.client.list_shared_files()
                    if result:
                        for file in result:
                            print(file)
                    else:
                        print("No shared files found")

                # ...Disconnect Peer...
                elif userChoice == "5":
                    peerMain.client.disconnect_peer()
                    connectedToPeer = False
                    print("Disconnected")
                    break

    except KeyboardInterrupt:  # CTRL + C To Exit
        print("Exiting...")

    except Exception as e:
        print(e)

    finally:
        print("Closing connection")
        if peerMain:
            centralizedServer_socket.send("DISCONNECT".encode())
            centralizedServer_socket.close()
            peerMain.client.disconnect_peer()
