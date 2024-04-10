import socket

CENTRAL_SERVER_IP = '0.0.0.0'  # Listen on all available interfaces
CENTRAL_SERVER_PORT = 8008  # Port to listen on


class Client:
    def __init__(self, username, address, port):
        self.username = username
        self.address = address
        self.port = port

def clientMessage(message, client_address, sock):
    # gets the command/inoput from the client
    messageSplit = message.decode().split()
    command = messageSplit[0]
    print("Command is:", command)

    if command == "register":
        # separate command 
        port = int(messageSplit[1])
        username = messageSplit[2]
        # get just the address
        address = client_address[0]

        # add client to list
        newClient = Client(username, address, port)
        clients.append(newClient)
        print(f"Registered: {client_address[0]}:{port}")

    elif command == "who":
        num_users = 0
        theList = ""
        for client in clients:
            num_users += 1
            theList += f"{client.username}: address: {client.address}, port: {client.port}\n"
        # send completed list 
        message = "\nTotal " + str(num_users) + " users(s) online:\n"
        message += theList
        sock.sendto(message.encode(), client_address)

    elif command == "exit":
        port = int(messageSplit[1])
        username = messageSplit[2]
        # remove from list to exit
        for client in clients:
            if client.username == username:
                clients.remove(client)
    
    elif command == "tell":
        recipient_username = messageSplit[1]
        found = False
        for client in clients:
            if client.username == recipient_username:
                recipient = client
                found = True
                break
        if found:
            response = f"INFO: {recipient.port}:{recipient.address}"
            sock.sendto(response.encode(), client_address)
        else:
            sock.sendto(f"NO INFO: User {recipient_username} is not online!".encode(), client_address)
        
    elif command == "shout":
        theList = "SHOUT\n"
        for client in clients:
            theList += f"{client.address}-{client.port}\n"
        # send completed list 
        sock.sendto(theList.encode(), client_address)
        

def main():
    # make the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind
    sock.bind((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
    print(f"Central server is running on {CENTRAL_SERVER_IP}:{CENTRAL_SERVER_PORT}")

    global clients
    clients = []

    while True:
        try:
            # get client input
            message, client_address = sock.recvfrom(4096)
            clientMessage(message, client_address, sock)
        except KeyboardInterrupt:
            print("Server is shutting down.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

    sock.close()

if __name__ == "__main__":
    main()
