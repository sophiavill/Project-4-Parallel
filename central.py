import socket

CENTRAL_SERVER_IP = '0.0.0.0'  # Listen on all available interfaces
CENTRAL_SERVER_PORT = 8008  # Port to listen on



def handle_client_message(message, client_address, sock):
    """Handle messages from clients."""
    message_parts = message.decode().split()
    command = message_parts[0]

    if command == "register":
        port = int(message_parts[1])
        username = message_parts[2]
        # Add the client to the list of active instances
        active_instances[f"{username}:{client_address[0]}:{port}"] = client_address
        print(f"Registered: {client_address[0]}:{port}")
    elif command == "list":
        theList = ""
        # Send the list of active instances to the client
        for key, value in active_instances.items():
            username, address, port = key.split(":")
            theList += f"Username: {username}, Address: {value[0]}, Port: {value[1]}\n"
        sock.sendto(theList.encode(), client_address)

    elif command == "exit":
        # take off the list
        port = int(message_parts[1])
        username = message_parts[2]
        if f"{username}:{client_address[0]}:{port}" in active_instances:
            active_instances.pop(f"{username}:{client_address[0]}:{port}")

def main():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the server's IP and port
    sock.bind((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

    print(f"Central server is running on {CENTRAL_SERVER_IP}:{CENTRAL_SERVER_PORT}")

    global active_instances
    active_instances = {}

    while True:
        try:
            # Wait for a message from a client
            message, client_address = sock.recvfrom(4096)  # Buffer size is 4096 bytes
            handle_client_message(message, client_address, sock)
        except KeyboardInterrupt:
            print("Server is shutting down.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

    sock.close()

if __name__ == "__main__":
    main()
