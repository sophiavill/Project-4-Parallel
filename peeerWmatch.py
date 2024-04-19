import socket
import threading
import queue
import sys
# import re
import select
import time
import random

# central server info
CENTRAL_SERVER_IP = '0.0.0.0' 
#CENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008

USERNAME = ""
IN_GAME = False
IS_SERVER = False
IS_CLIENT = False
CLIENT_SOCKET = 0
SOC_LIST = []
SERVER_SOCKET = 0
SOCK = None
READABLE = None
CURRENT_GAME = None

currentMessage = ""

class Game:
    def __init__(self):
        self.player1_name = " "
        self.player2_name = " "
        self.board = self.init_board()
        self.player1_faction = " "
        self.player2_faction = " "
        self.current_player = -1
        self.is_active = False
        self.valid_moves = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
        self.played_moves = [False] * 9
        self.player_spot = [" "] * 9

    def init_board(self):
        return [['.' for _ in range(3)] for _ in range(3)]
    

#----------------------------------------------------------------------------------------------------------------

def print_client_side(message):
    for sock in SOC_LIST:
        if sock != SERVER_SOCKET and sock != sys.stdin:
            sock.sendall(message.encode())

def print_board(current_game, name):
    board_str = f"{current_game.player1_name}: {current_game.player1_faction} \t\t {current_game.player2_name}: {current_game.player2_faction}\n"
    board_str += "\n    1  2  3\n"
    for i in range(3):
        row_label = chr(ord('A') + i)
        board_str += row_label + "  "
        for j in range(3):
            board_str += " " + current_game.board[i][j] + " "
        board_str += "\n"

    if(name == "server"):
        print(board_str)
        print(USERNAME + ">", end="")
    else:
        print_client_side(board_str)

def check_win(board, player):
   # rows
   for i in range(3):
       if board[i][0] == player and board[i][1] == player and board[i][2] == player:
           return True
   # coll
   for j in range(3):
       if board[0][j] == player and board[1][j] == player and board[2][j] == player:
           return True
   # diag
   if (board[0][0] == player and board[1][1] == player and board[2][2] == player) or \
      (board[0][2] == player and board[1][1] == player and board[2][0] == player):
       return True
   return False

def check_draw(board):
   for i in range(3):
       for j in range(3):
           if board[i][j] == '.':
               return False  # if any cell is empty, game is not a draw
   return True  # if all cells are filled and no winner, it's a draw

def play_tic_tac_toe():
   board = init_board()
   current_player = '#'

   while True:
       print_board(board)
       print("Player", current_player, "'s turn. Enter row and column (e.g., A1): ")
       move = input().strip().upper()

       row, col = move[0], int(move[1]) - 1

       row_index = ord(row) - ord('A')
       column_index = col

       if row_index < 0 or row_index >= 3 or column_index < 0 or column_index >= 3 or board[row_index][column_index] != '.':
           print("Invalid move. Try again.")
           continue

       board[row_index][column_index] = current_player

       if check_win(board, current_player):
           print_board(board)
           print("Player", current_player, "wins!")
           break

       if check_draw(board):
           print_board(board)
           print("It's a draw!")
           break

       current_player = 'O' if current_player == '#' else '#'


#----------------------------------------------------------------------------------------------------------------

# get message from serevr
def receiveMessages(sock, message_queue):
    global IS_SERVER
    global USERNAME
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
                global IN_GAME
                IN_GAME = True
                global IS_CLIENT
                IS_CLIENT = True

                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]
                other_player_name = messageSplit[3]

                retries = 5
                delay = 2
                sock = None

                for attempt in range(retries):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((address, port))
                        break 
                    except ConnectionRefusedError:
                        print(f"Trying to connect to game...")
                        time.sleep(delay) 

                if not sock:
                    raise Exception("Server is not accepting connections")
                
                print("Success! Game started with:", other_player_name)
                print_game_menu(1)
                # print board game 

                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((address, port))
                global CLIENT_SOCKET
                CLIENT_SOCKET = client_socket

            elif message.startswith("SERVER"):
                # global IS_SERVER
                IS_SERVER = True
                IN_GAME = True

                messageSplit = message.split(":")
                port = int(messageSplit[1])
                address = messageSplit[2]
                other_player_name = messageSplit[3]
               
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                global SERVER_SOCKET
                SERVER_SOCKET = server_socket
                server_socket.bind((address, port))
                server_socket.listen(2)
                print(f"Server started on {address}:{port}. Waiting for connections...")
                sockets_list = [server_socket]
                global SOC_LIST
                SOC_LIST = sockets_list
                
                printedBool = False
                try:
                    while True:
                        # Use select to handle input from multiple sockets (including stdin)
                        readable, _, _ = select.select(sockets_list, [], [])
                        global READABLE
                        READABLE = readable
                        for source in readable:
                            if source == server_socket:
                                client_socket, client_address = server_socket.accept()
                                sockets_list.append(client_socket)
                                if(printedBool == False):
                                    global CURRENT_GAME
                                    
                                    current_game = Game()
                                    CURRENT_GAME = current_game

                                    print("\nSuccess! Game started with:", other_player_name)
                                    print_game_menu(1)

                                    message = "Game pices have been randomly assigned: \n"
                                    message += "X will go first.\n\n"
                                    factions = ['X', 'O']
                                    random.shuffle(factions)
                                    current_game.player1_faction, current_game.player2_faction = factions
                                    current_game.player1_name = USERNAME
                                    current_game.player2_name = other_player_name
                                    message += f"Player 1 is {current_game.player1_name}: {current_game.player1_faction}\n"
                                    message += f"Player 2 is {current_game.player2_name}: {current_game.player2_faction}\n"

                                    print_client_side(message)
                                    print(message)
                                    
                                    print_board(current_game, "server")
                                    # print("printing heree 8888 " + USERNAME + "> ", end="")

                                    print_board(current_game, "client")
                                    
                                    printedBool = True
                            else:
                                # looking at client INPUT SERVER side
                                data = source.recv(1024)
                                clean_data = data.decode().strip() 
                                
                                for move in current_game.valid_moves:
                                        if move == clean_data:
                                            print("This is a game move")
                                            # this is a game move. we need to see if it is this players turn

                                # if clean_data != "exit":
                                #     # rn just echo
                                #     print(clean_data + "\n" + USERNAME + "> ", end="")
                                #     source.sendall(data)
                                #     for move in current_game.valid_moves:
                                #         if move == clean_data:
                                #             print("This is a game move")
                                if clean_data == "exit":
                                    # Remove client from the list and close the socket if connection is lost
                                    # send to client 
                                    #print_client_side("EXITING")
                                    print("Trying to exit rn in here")
                                    
                                    sockets_list.remove(source)
                                    source.close()
                                    server_socket.close()
                                    IN_GAME = False
                                    IS_SERVER = False
                                    print(f"Welcome back to the game server!")
                                    # tell the other user 
                                    print_client_side('GAMEOVER')

                                    #tell the game server
                                    message = f"GAMEOVER {current_game.player1_name} {current_game.player2_name}".encode()
                                    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
                                    # get back into the server thread
                                    IN_GAME = False
                                    IS_SERVER = False
                                    message_queue = queue.Queue()
                                    threading.Thread(target=receiveMessages, args=(SOCK, message_queue), daemon=True).start()
                                    user_interface(SOCK, listen_port, message_queue)
                                    SOCK.close()

                except KeyboardInterrupt:
                    # Close all sockets
                    for sock in sockets_list:
                        if sock != sys.stdin:
                            sock.close()
                    print("Server stopped.")

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
            
            elif message.startswith("GAMEOVER"):
                IN_GAME = False
                IS_CLIENT = False
                message_queue = queue.Queue()
                threading.Thread(target=receiveMessages, args=(SOCK, message_queue), daemon=True).start()
                user_interface(SOCK, listen_port, message_queue)
                SOCK.close()
    
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


# communicate w the match server
            
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

def print_game_menu(number):
    print("\nGame Menu:")
    print("  tell  <msg>             # tell <message>")
    print("  exit                    # quit the system")
    print("  refresh                 # print the game board")
    print("  ?                       # print this message")
    if(number != 1):
        print(USERNAME + "> ", end="")
    else:
        print("\n\n")

def user_interface(sock, listen_port, message_queue):
    threading.Thread(target=printMessage, args=(message_queue,), daemon=True).start()

    print_menu()
    
    while True:
        allCommand = input()
        commandSplit = allCommand.split()
        if commandSplit:
            command = commandSplit[0]

# in game functions
#--------------------------------------------------------------------------------------------------------------------------------------
        global IN_GAME
        global IS_SERVER
        if(IN_GAME == True):
            
            # looking at client INPUT client side
            if(IS_CLIENT == True):
                if(command == "?"):
                    print_game_menu(2)
                elif(command == "tell"):
                    if len(commandSplit) >= 2:
                        message = f"{USERNAME}: {' '.join(commandSplit[1:])}"
                        CLIENT_SOCKET.sendall(message.encode())
                    else:
                        print("Missing message.")
                else:
                    print("Comand not supported. ")
                
                print(USERNAME + "> ", end="", flush=True)
                    # CLIENT_SOCKET.sendall(allCommand.encode())
                    # print(USERNAME + "> ", end="")


            # looking at server INPUT      
            elif(IS_SERVER == True):
                # looking at server input
                print_client_side(allCommand)
                
                if(command == "?"):
                    print_game_menu(2)
                elif(command == "tell"):
                    if len(commandSplit) >= 2:
                        message = f"{USERNAME}: {' '.join(commandSplit[1:])}"
                        print_client_side(message)
                    else:
                        print("Missing message.")
                elif(command == "exit"):
                    for source in READABLE:
                         if source != SERVER_SOCKET:
                            SOC_LIST.remove(source)
                            source.close()
                            SERVER_SOCKET.close()
                            IN_GAME = False
                            IS_SERVER = False
                            print(f"Welcome back to the game server!")

                            print_client_side('GAMEOVER')
                            #tell the game server
                            message = f"GAMEOVER {CURRENT_GAME.player1_name} {CURRENT_GAME.player2_name}".encode()
                            sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
                            # get back into the server thread
                            IN_GAME = False
                            IS_SERVER = False
                            message_queue = queue.Queue()
                            threading.Thread(target=receiveMessages, args=(SOCK, message_queue), daemon=True).start()
                            user_interface(SOCK, listen_port, message_queue)
                            SOCK.close()
                else:
                    print("Comand not supported. ")
                    # print(USERNAME + "> ", end="", flush=True)
                print(USERNAME + "> ", end="", flush=True)
#--------------------------------------------------------------------------------------------------------------------------------------
# regular server functions
                            
        else:
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
    global SOCK
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", listen_port))
    SOCK = sock
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