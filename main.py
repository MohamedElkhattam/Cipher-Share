import os

from fileshare_client import FileShareClient

if __name__ == "__main__":
    while True:
        userChoice = input("1. REGISTER\n"  "2. LOGIN\n"
                           "3. UPLOAD\n"    "4. DOWNLOAD\n"
                           "5. SEARCH\n"    "6. EXIT\n")
        client = FileShareClient()
        client.connect_to_peer(('localhost', 5000))

        # Authentication Section
        if userChoice == "1":
            username = input("Please enter your username and password\nUsername :")
            password = input("Password :")
            client.register_user(username, password)

        elif userChoice == "2":
            username = input("Please enter your username and password\nUsername :")
            password = input("Password :")
            client.login_user(username, password)

        # File Handling Section
        elif userChoice == "3":
            path = input("Please enter path of the file to be uploaded\nPath :")
            client.upload_file(path)


        elif userChoice == "4":
            filename = input("Please enter name of the file to be downloaded\nFilename: ")
            path = input("Where you want to save your file\nPath :")
            client.download_file(filename, path)

            # result = client.search_files(path)
            # if result:
            #     print("Downloading...")
            #     client.download_file()
            # else:
            #     print("File not found.")

        elif userChoice == "5":
            name = input("Please enter file name\nName: ")
            client = FileShareClient()
            result = client.search_files(name)
            if result:
                choice = input("Want to download file?\n"
                               "Yes / No\n")
                if choice.lower() == "yes":
                    print("Downloading...")
                    client.download_file(name)
                else:
                    continue

        # Exit and wrong commands
        elif userChoice == "6":
            print("See you soon")
            break

        else:
            print("Invalid input\n"
                  "Try another option :(")
            break
