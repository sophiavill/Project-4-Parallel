import socket
import threading
import queue
import sys
import re
import select

# central server info
CENTRAL_SERVER_IP = '0.0.0.0' 
#CENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008
USERNAME = ""
IN_GAME = False

currentMessage = ""

def receiveMessages(sock, message_queue):
    while True:
        try:
            message, _ = sock.recvfrom(4096) 
            message = message.decode()
            
            if message.startswith("MATCH"):
                
                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]
            
                messageToSend = f"{currentMessage} \nDo you want to accept the game from {USERNAME}?\n(accept {USERNAME} or decline {USERNAME})"
                #response = input("Accept the match? (accept/decline): ") 
                sock.sendto(messageToSend.encode(), (address, port))
                print("Invite sent. \n" + USERNAME + ">", end="")
                
            elif message.startswith("DECLINE"):
                
                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]
            
                messageToSend = f"{currentMessage}" 
                sock.sendto(messageToSend.encode(), (address, port))
                print("Invite was declined. \n" + USERNAME + ">", end="")

            elif message.startswith("ACCEPT"):
                print("YOU ARE THE player")
                # use {recipient.port}:{recipient.address}"
                # to connect to server 
                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]

                print(f"The server we are connecting to: {port} at {address}")
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((address, port))

                message = "Hello, server!"
                client_socket.sendall(message.encode())
                print(f"Sent: {message}")
                # Receive the response from the server
                data = client_socket.recv(1024)
                print(f"Received: {data.decode()}")
                
                print("heyyyy")
                
                # Close the socket to clean up
                client_socket.close()
                print("Connection closed.")


                

            elif message.startswith("SERVER"):
                print("YOU ARE THE SERVER")
                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]

                # Create a socket object using IPv4 and TCP protocol
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Bind the socket to the provided address and port
                server_socket.bind((address, port))
                # Start listening for incoming connections (max 5 clients in the waiting queue)
                server_socket.listen(5)
                print(f"Server started on {address}:{port}. Waiting for connections...")
                # List of socket objects to monitor for incoming data
                sockets_list = [server_socket, sys.stdin]
                try:
                    while True:
                        # Use select to handle input from multiple sockets (including stdin)
                        readable, _, _ = select.select(sockets_list, [], [])
                        for source in readable:
                            if source == server_socket:
                                # Handle the server socket
                                client_socket, client_address = server_socket.accept()
                                print(f"Connected by {client_address}")
                                sockets_list.append(client_socket)
                            elif source == sys.stdin:
                                # Handle standard input
                                msg = sys.stdin.readline()
                                # Send input to all connected clients
                                for sock in sockets_list:
                                    if sock != server_socket and sock != sys.stdin:
                                        sock.sendall(msg.encode())
                            else:
                                # Handle client socket
                                data = source.recv(1024)
                                if data:
                                    print(f"Received from username: {data.decode().strip()}")
                                    
                                    source.sendall(data)
                                else:
                                    # Remove client from the list and close the socket if connection is lost
                                    sockets_list.remove(source)
                                    source.close()
                                    print(f"Welcome back to the game server!")
                                    # get back into the server thread
                                    message_queue = queue.Queue()
                                    threading.Thread(target=receiveMessages, args=(sock, message_queue), daemon=True).start()
                                    user_interface(sock, listen_port, message_queue)
                                    sock.close()

            
                except KeyboardInterrupt:
                    # Close all sockets
                    for sock in sockets_list:
                        if sock != sys.stdin:
                            sock.close()
                    print("Server stopped.")
               


                # messageSplit = message.split(":")
                # port = int(messageSplit[1])
                # address = messageSplit[2]

                # messageToSend = f"{currentMessage}"
                # sock.sendto(messageToSend.encode(), (address, port))
                # print("Invite was accepted. \n" + USERNAME + ">", end="")


            elif message.startswith("INFO"):
                # INFO: {recipient.port}:{recipient.address} get in this format
                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]

                messageToSend = f"{USERNAME}: {currentMessage}"
                sock.sendto(messageToSend.encode(), (address, port))
                print("Message sent.\n" + USERNAME + "> ", end="")

            elif message.startswith("NO INFO"):
                # NO INFO: User {recipient_username} is not online! get in this format
                messageParts = message.split(":", 1)
                print(messageParts[1] + "\n" + USERNAME + "> ", end="")

            elif message.startswith("SHOUT"):
                print(message)
                lines = message.split('\n')
                for line in lines[1:]:
                    lineSplit = line.split('-')
                    if len(lineSplit) >= 2:
                        address = lineSplit[0]
                        port = int(lineSplit[1])
                        finalMessage = f"*{USERNAME}*: " + currentMessage
                        sock.sendto(finalMessage.encode(), (address, port))
                print("Message sent.\n" + USERNAME + "> ", end="")
                
            else:
                message_queue.put(f"\n{message}")

        except Exception as e:
            message_queue.put(f"An error occurred: {e}")
            break


def printMessage(message_queue):
    while True:
        message = message_queue.get()
        if message == "exit":
            break
        print(message)
        print(USERNAME + "> ", end="", flush=True) 

def serverRegister(sock, own_port):
    # send username + port to the server 

    welcome = ("\n\n\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
           + "\t\t%                                         %\n"
           + "\t\t%             Welcome to the P2P          %\n"
           + "\t\t%         Online Tic-tac-toe Server       %\n"
           + "\t\t%                                         %\n"
           + "\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
    print(welcome)

    username = input("> Enter your username: ")
    
    global USERNAME 
    USERNAME = username

    message = f"register {own_port} {username}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def whoCommand(sock):
    # get users from server
    message = "who".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def shoutCommand(sock):
    message = "shout".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def tellCommand(recipient, sock, listen_port):
    message = f"tell {recipient}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def matchCommand(message, recipient, sock, listen_port):
    #ensures server has the username of the recipient, message, lisitening port, and username of sender
    #message =f"match {recipient} {message} {USERNAME}".encode()
    message = f"match {recipient} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def declineCommand(message, recipient, sock, listen_port):
    message = f"decline {recipient} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def acceptCommand(message, recipient, sock, listen_port):
    message = f"accept {recipient} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
    
def exitCommand(sock, own_port):
    message = f"exit {own_port} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def print_menu():
    print("\nMenu:")
    print("  who                     # List all online users")
    print("  shout <msg>             # shout <msg> to every one online")
    print("  tell <name> <msg>       # tell user <name> message")
    print("  exit                    # quit the system")
    print("  match <name>            # Try to start a game")
    print("  accept <name>           # Accept an invite")
    print("  decline <name>          # Decline an invite")
    print("  ?                       # print this message")
    print(USERNAME + "> ", end="")

def user_interface(sock, listen_port, message_queue):
    threading.Thread(target=printMessage, args=(message_queue,), daemon=True).start()

    print_menu()
    
    while True:
        allCommand = input()
        commandSplit = allCommand.split()
        command = commandSplit[0]

        if command == "who":
            whoCommand(sock)

        elif command == "shout":
            if len(commandSplit) >= 2:
                message = ' '.join(commandSplit[1:])
                global currentMessage
                currentMessage = message
                shoutCommand(sock)
            else:
                print("Missing message")
                print(USERNAME + "> ", end="")

        elif command == "tell":
            if len(commandSplit) >= 3:
                commandSplit = allCommand.split(" ", 2)
                recipient = commandSplit[1] 
                message = commandSplit[2] 
                # global currentMessage
                currentMessage = message
                tellCommand(recipient, sock, listen_port)
            else:
                print("Missing user or message")
                print(USERNAME + "> ", end="")
            

        elif command == "exit":
            message_queue.put("exit")
            exitCommand(sock, listen_port)
            break
        
        elif command == "?":
            print_menu()
        
        elif command == "match":
            if len(commandSplit) >= 2:
                player2 = commandSplit[1]
                message = f"match invite from:{USERNAME}:{socket.gethostbyname(socket.gethostname())}:{listen_port}"
        
        
                matchCommand(message, player2, sock, listen_port)
                currentMessage = message
                
            else:
                print("Missing recipient username.")
                print(USERNAME + "> ", end="")

        elif command == "decline":
            if len(commandSplit) >= 2:
                player2 = commandSplit[1]
                message = f"{USERNAME} has declined your invite!"
                
                declineCommand(message, player2, sock, listen_port)
                currentMessage = message
            
            else:
                print("Missing recipient username.")
                print(USERNAME + "> ", end="")

        elif command == "accept":
            if len(commandSplit) >= 2:
                player2 = commandSplit[1]
                message = f"{USERNAME} has accepted your invite!"

                acceptCommand(message, player2, sock, listen_port)
                currentMessage = message

            else:
                print("Missing recipient username.")
                print(USERNAME + "> ", end="")

    
        #the accept command will be the exact same
        #WITH the connection functionality and of course a different message
                 
        else:
            print("Command not supported.")
            print(USERNAME + "> ", end="")

#Experimental functionality
#allows peer to listen to other peers (I hope)
def tcpServer(listen_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', listen_port))
    server_socket.listen()
    print("This Peer is listening on port", listen_port)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        threading.Thread(target=handlePeer, args=(client_socket,)).start()

#handle peer comms
def handlePeer(client_socket):
    with client_socket:
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                recievedMsg = data.decode()
                print("Received:", data.decode())
        except Exception as e:
            print("Peer handling error:", e)


def main(listen_port):

    # #TCP setup - should allow for peer to peer comms
    # threading.Thread(target=tcpServer, args=(listen_port,), daemon=True).start()

    #UDP code - peer to central
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", listen_port))

    serverRegister(sock, listen_port)

    message_queue = queue.Queue()
    threading.Thread(target=receiveMessages, args=(sock, message_queue), daemon=True).start()

    user_interface(sock, listen_port, message_queue)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py [listening port]")
        sys.exit(1)
    listen_port = int(sys.argv[1])
    main(listen_port)