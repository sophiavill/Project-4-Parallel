import socket
import threading
import queue
import sys

# central server info
CENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008
USERNAME = ""
MESSAGE = ""

def receiveMessages(sock, message_queue):
    while True:
        try:
            message, _ = sock.recvfrom(4096) 
            decoded_message = message.decode()

            if decoded_message.startswith("Recipient port"):
                # Do something with the message indicating recipient's port
                # For example, you can print it, extract the port, etc.
                print("++++++++Received recipient's port:", decoded_message)
            else:
                message_queue.put(f"\n{decoded_message}")

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
    print("  ?                       # print this message")
    print(USERNAME + "> ", end="")

def user_interface(sock, listen_port, message_queue):
    threading.Thread(target=printMessage, args=(message_queue,), daemon=True).start()

    print_menu()
    
    while True:
        command = input()
        commandSplit = command.split()
        command = commandSplit[0]

        if command == "who":
            whoCommand(sock)

        elif command == "shout":
            print("shout coming soon")

        elif command == "tell":
            recipient = commandSplit[1] 
            tellCommand(recipient, sock, listen_port)
            # peer_ip = input("> Enter the peer's IP address: ")
            # peer_port = int(input("> Enter the peer's port: "))
            # message = input("> Enter your message: ")
            # sock.sendto(message.encode(), (peer_ip, peer_port))

        elif command == "exit":
            message_queue.put("exit")  # Signal to stop the message printing thread
            exitCommand(sock, listen_port)
            break
        
        elif command == "?":
            print_menu()
       
        else:
            print("Command not supported.")
            print(USERNAME + "> ")

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