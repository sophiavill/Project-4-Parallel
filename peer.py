import socket
import threading
import queue
import sys

# central server info
CENTRAL_SERVER_IP = '0.0.0.0' 
#ENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008
USERNAME = ""
IN_GAME = False


currentMessage = ""


def receiveMessages(sock, message_queue):
    while True:
        try:
            message, _ = sock.recvfrom(4096) 
            message = message.decode()

            if message.startswith("INFO"):
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

def exitCommand(sock, own_port):
    message = f"exit {own_port} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def print_menu():
    print("\nMenu:")
    print("  who                     # List all online users")
    print("  shout <msg>             # shout <msg> to every one online")
    print("  tell <name> <msg>       # tell user <name> message")
    print("  exit                    # quit the system")
    print( "  match <name> <b|w> [t]  # Try to start a game")
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
            # match <name> <b|w> [t]
            if len(commandSplit) >= 3:
                player2 = commandSplit[1]
                color = commandSplit[2]
                playTime = 600
                if len(commandSplit) == 4:
                    playTime = int(commandSplit[3])

                print("Player 2: " + player2 + " color of me " + color + "play time " + str(playTime))

                # ask the server if that user can play
                # sever will send message asking "can you play"
                # then the client will get the print out to match 
                # we will have a pending list and active game object. only one active game
                # check if in the pending, then go into gameplay
                # connect to other user  
              
            else:
                print("Missing information")
                print(USERNAME + "> ", end="")


       
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