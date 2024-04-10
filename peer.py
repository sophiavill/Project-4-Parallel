import socket
import threading
import queue
import sys

CENTRAL_SERVER_IP = '128.186.120.158'  # Central server's IP address
CENTRAL_SERVER_PORT = 8008  # Central server's port
USERNAME = ""

def receive_messages(sock, message_queue):
    while True:
        try:
            message, _ = sock.recvfrom(4096)  # Buffer size is 4096 bytes
            message_queue.put(f"\n{message.decode()}")
        except Exception as e:
            message_queue.put(f"An error occurred: {e}")
            break

def print_messages_from_queue(message_queue):
    while True:
        message = message_queue.get()
        if message == "exit":
            break
        print(message)
        print("> ", end="", flush=True)  # Ensure prompt is printed after message

def register_with_central_server(sock, own_port):
    # Send registration message to the central server
    choice = input("> Enter your username: ")
    global USERNAME 
    USERNAME = choice
    message = f"register {own_port} {choice}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def request_active_instances(sock):
    # Request the list of active instances from the central server
    message = "list".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def request_exit(sock, own_port):
    # Request the list of active instances from the central server

    message = f"exit {own_port} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))


def print_menu():
    print("\nMenu:")
    print("1. Send a message")
    print("2. List active instances")
    print("3. Exit")
    print("?")
    print("> ", end="")

def user_interface(sock, listen_port, message_queue):
    print("You can start sending messages. Type 'exit' to quit.")
    threading.Thread(target=print_messages_from_queue, args=(message_queue,), daemon=True).start()

    print_menu()
    
    while True:
        choice = input()
        if choice == "1":
            #ask for their name 
            #
            peer_ip = input("> Enter the peer's IP address: ")
            peer_port = int(input("> Enter the peer's port: "))
            message = input("> Enter your message: ")
            sock.sendto(message.encode(), (peer_ip, peer_port))
        elif choice == "2":
            # This is a placeholder. Implement requesting and displaying the list of active instances here.
            request_active_instances(sock)
        elif choice == "?":
            print_menu()
        elif choice == "3":
            message_queue.put("exit")  # Signal to stop the message printing thread
            request_exit(sock, listen_port)
            break
        else:
            print("> Invalid choice. Please enter 1, 2, or 3.")

def main(listen_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", listen_port))

    register_with_central_server(sock, listen_port)

    message_queue = queue.Queue()
    threading.Thread(target=receive_messages, args=(sock, message_queue), daemon=True).start()

    user_interface(sock, listen_port, message_queue)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py [listening port]")
        sys.exit(1)
    listen_port = int(sys.argv[1])
    main(listen_port)