import socket
import threading
import queue
import sys
import re

# central server info
CENTRAL_SERVER_IP = '0.0.0.0' 
#CENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008
USERNAME = ""
IN_GAME = False


currentMessage = ""

#my idea has to have lists to store the following, but this could be better stored as client lists in central
#pendingInvites = []
#pendingResponse = []


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
                print("Invite sent. \n" + USERNAME + ">", end="")

            

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
                message = f"{USERNAME} has decline your invite!"
                
                declineCommand(message, player2, sock, listen_port)
                currentMessage = message
            
            else:
                print("Missing recipient username.")
                print(USERNAME + "> ", end="")
    
        #the accept command will be the exact same
        #WITH the connection functionality and of course a different message
                 
        else:
            print("Command not supported.")
            print(USERNAME + "> ", end="")

def main(listen_port):
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
