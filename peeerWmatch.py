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

EXIT_NOW = False


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
        self.current_player = ""
        self.is_active = False
        self.valid_moves = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
        self.played_moves = [False] * 9
        self.player_spot = [" "] * 9
        self.winner = ""
        self.loser = ""
        self.draw = False

    def init_board(self):
        return [['.' for _ in range(3)] for _ in range(3)]
    

#----------------------------------------------------------------------------------------------------------------

def print_client_side(message):
    for sock in SOC_LIST:
        if sock != SERVER_SOCKET and sock != sys.stdin:
            sock.sendall(message.encode())

def print_board(current_game, name):
    board_str = f"\n\n{current_game.current_player}'s turn!"
    board_str += f"\n{current_game.player1_name}: {current_game.player1_faction} \t\t {current_game.player2_name}: {current_game.player2_faction}\n"
    board_str += "\n    1  2  3\n"
    for i in range(3):
        row_label = chr(ord('A') + i)
        board_str += row_label + "  "
        for j in range(3):
            board_str += " " + current_game.board[i][j] + " "
        board_str += "\n"

    if(name == "server"):
        # print(board_str)
        print(board_str + USERNAME + ">", end="")
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

def gameplay(move, player_type, faction):
    global CURRENT_GAME

    row, col = move[0], int(move[1]) - 1
    row_index = ord(row) - ord('A')
    column_index = col

    if row_index < 0 or row_index >= 3 or column_index < 0 or column_index >= 3 or CURRENT_GAME.board[row_index][column_index] != '.':
        if(player_type == "server"):
            print("Invalid move. Try again. \n" + USERNAME + "> ", end="")
        else:
            errorMsg = "Invalid move. Try again."
            print_client_side(errorMsg)
        return

    CURRENT_GAME.board[row_index][column_index] = faction
    
    if(player_type == "server"):
        CURRENT_GAME.current_player = CURRENT_GAME.player2_name
    else:
        CURRENT_GAME.current_player = CURRENT_GAME.player1_name

    print_board(CURRENT_GAME, "server")
    print_board(CURRENT_GAME, "client")

    if(check_win(CURRENT_GAME.board, faction)):
        if(player_type == "server"):
            message = "\nGame over! " + CURRENT_GAME.player1_name + " won and " + CURRENT_GAME.player2_name + " lost.\n"
            CURRENT_GAME.winner = CURRENT_GAME.player1_name
            CURRENT_GAME.loser = CURRENT_GAME.player2_name
            print(message)
            print_client_side(message)
        else:
            message = "\nGame over! " + CURRENT_GAME.player2_name + " won and " + CURRENT_GAME.player1_name + " lost.\n"
            CURRENT_GAME.loser = CURRENT_GAME.player1_name
            CURRENT_GAME.winner = CURRENT_GAME.player2_name
            print(message)
            print_client_side(message)
        
        print_client_side('EXIT_NOW')
    
    elif(check_draw(CURRENT_GAME.board)):
        message = "Game over! Its a draw!\n"
        print(message)
        print_client_side(message)
        CURRENT_GAME.draw = True

        print_client_side('EXIT_NOW')


    
    
#----------------------------------------------------------------------------------------------------------------
def exitFuncServer(source):
    SOC_LIST.remove(source)
    source.close()
    SERVER_SOCKET.close()
    global IN_GAME, IS_SERVER
    IN_GAME = False
    IS_SERVER = False
    print(f"Welcome back to the game server!")

    # print("Active Threads:")
    # for thread in threading.enumerate():
    #     print(thread.name)

    print_client_side('GAMEOVER')

    #tell the game server
    if(CURRENT_GAME.draw):
        message = f"DRAW {CURRENT_GAME.player1_name} {CURRENT_GAME.player2_name}".encode()
    else:
        message = f"GAMEOVER {CURRENT_GAME.winner} {CURRENT_GAME.loser}".encode()
    SOCK.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
    # get back into the server thread
    IN_GAME = False
    IS_SERVER = False
    message_queue = queue.Queue()
    threading.Thread(target=receiveMessages, args=(SOCK, message_queue), daemon=True).start()
    user_interface(SOCK, listen_port, message_queue)
    SOCK.close()

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
                
                print("\nSuccess! Game started with:", other_player_name)
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
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # enable address reuse
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
                                # Handle the server socket
                                client_socket, client_address = server_socket.accept()
                                # print(f"Connected by {client_address}")
                                sockets_list.append(client_socket)
        
                                if(printedBool == False):
                                    current_game = Game()

                                    print("\nSuccess! Game started with:", other_player_name)

                                    # get the server the game menu
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

                                    if (current_game.player1_faction == 'X'):
                                        current_game.current_player = current_game.player1_name
                                    else:
                                        current_game.current_player = current_game.player2_name


                                    print_client_side(message)
                                    print(message)

                                    print_board(current_game, "server")
                                    
                                    print_board(current_game, "client")

                                    printedBool = True
                                    global CURRENT_GAME
                                    CURRENT_GAME = current_game
                            else:
                                # Handle client socket
                                data = source.recv(1024)
                                clean_data = data.decode().strip()

                                commandSplit = clean_data.split()
                                if commandSplit:
                                    command = commandSplit[0]
                                else:
                                    command = " "
                                
                                if data:
                                    # print(f"Received from username: {clean_data}")

                                    if(command == "exit"):
                                        exitFuncServer(source)
                                    if command == "MOVE":
                                        # check if their turn
                                        if(CURRENT_GAME.current_player != USERNAME):
                                            # gameplay(move, type, player_faction)
                                            gameplay(commandSplit[1], "client", CURRENT_GAME.player2_faction)
                                        else:
                                            print_client_side("It is not your turn!")

                                    else:
                                        clean_send = clean_data + "\n" + USERNAME + "> "
                                        print(clean_send, end="")

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
            
            elif message.startswith("EXIT_NOW"):
                    command = "exit"
                    CLIENT_SOCKET.sendall(command.encode())
    
            else:
                message_queue.put(f"\n{message}")
                # print(USERNAME + "> ", end="")

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

    tic = r""" 
       %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


                                     ██████╗ ██████╗ ██████╗ 
                                     ██╔══██╗╚════██╗██╔══██╗
                                     ██████╔╝ █████╔╝██████╔╝
                                     ██╔═══╝ ██╔═══╝ ██╔═══╝ 
                                     ██║     ███████╗██║     
                                     ╚═╝     ╚══════╝╚═╝     
                        


         ████████╗██╗ ██████╗    ████████╗ █████╗  ██████╗    ████████╗ ██████╗ ███████╗
         ╚══██╔══╝██║██╔════╝    ╚══██╔══╝██╔══██╗██╔════╝    ╚══██╔══╝██╔═══██╗██╔════╝
            ██║   ██║██║            ██║   ███████║██║            ██║   ██║   ██║█████╗  
            ██║   ██║██║            ██║   ██╔══██║██║            ██║   ██║   ██║██╔══╝  
            ██║   ██║╚██████╗       ██║   ██║  ██║╚██████╗       ██║   ╚██████╔╝███████╗
            ╚═╝   ╚═╝ ╚═════╝       ╚═╝   ╚═╝  ╚═╝ ╚═════╝       ╚═╝    ╚═════╝ ╚══════╝

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        """
                                                                                  

    # welcome = ("\n\n\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    #        + "\t\t%                                         %\n"
    #        + "\t\t%             Welcome to the P2P          %\n"
    #        + "\t\t%         Online Tic-tac-toe Server       %\n"
    #        + "\t\t%                                         %\n"
    #        + "\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
    print("\n\n\t\t" + tic + "\n")

    username = input("> Enter your username: ")
    
    global USERNAME 
    USERNAME = username

    message = f"register {own_port} {username}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def whoCommand(sock):
    # get users from server
    message = "who".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

def scoreCommand(sock):
    message = "score".encode()
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
    message = f"exit {own_port} {USERNAME}"
    message = f"exit {own_port} {USERNAME}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))
    print("May need to enter to confirm > ", end="")

    global EXIT_NOW
    EXIT_NOW = True
    while EXIT_NOW:
        print("HERE")
        sys.exit(0)

def print_menu():
    print("\nMenu:")
    print("  who                     # List all online users")
    print("  shout <msg>             # shout <msg> to every one online")
    print("  tell <name> <msg>       # tell user <name> message")
    print("  exit                    # quit the system")
    print("  match <name>            # Try to start a game")
    print("  accept <name>           # Accept an invite")
    print("  decline <name>          # Decline an invite")
    print("  score                   # Print the scoreboard")
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
        # print("Active Threads:")
        # for thread in threading.enumerate():
        #     print(thread.name)

 
        allCommand = input()
        commandSplit = allCommand.split()
        if commandSplit:
            command = commandSplit[0]
        else:
            command = " "

# in game functions
#--------------------------------------------------------------------------------------------------------------------------------------
        global IN_GAME
        global IS_SERVER

        if(IN_GAME == True):
            valid_moves = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]

            if(IS_CLIENT == True):
                message = allCommand
                # CLIENT_SOCKET.sendall(message.encode())

                if command == "tell":
                    message = f"\n{USERNAME}: {' '.join(commandSplit[1:])}"
                    CLIENT_SOCKET.sendall(message.encode())
                    print(USERNAME + "> ", end="")
                elif(command == "?"):
                    print_game_menu(2)
                elif(command == "exit"):
                    CLIENT_SOCKET.sendall(command.encode())
                elif(command in valid_moves):
                    message = f"MOVE {command}"
                    CLIENT_SOCKET.sendall(message.encode())

                #  elif to chec if valiud move, if it is: we will send to the server 
                    # send to serervr
                else:
                    toSend = "Command not supported.\n" + USERNAME + "> "
                    print(toSend, end="")
            
                    
            if(IS_SERVER == True):
                if(command == "tell"):
                    message = f"\n{USERNAME}: {' '.join(commandSplit[1:])}"
                    print_client_side(message)
                    print(USERNAME + "> ", end="")
                elif(command == "?"):
                    print_game_menu(2)
                elif(command == "exit"):
                    # all exiting has to happen inside server loop
                    print_client_side('EXIT_NOW')
                elif(command in valid_moves):
                    # check if my turn, do stuff based on that
                    if(CURRENT_GAME.current_player == USERNAME):
                        gameplay(command, "server", CURRENT_GAME.player1_faction)
                            
                    else:
                        print("It is not your turn!\n" + USERNAME + "> ", end="")

                    
                else:
                    toSend = "Command not supported.\n" + USERNAME + "> "
                    print(toSend, end="")

#--------------------------------------------------------------------------------------------------------------------------------------
# regular server functions
                            
        else:
            if command == "who":
                whoCommand(sock)
            elif command == "score":
                scoreCommand(sock)

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
                print("EXIT FROM input side")
                message_queue.put("exit")
                exitCommand(SOCK, listen_port)
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
                toSend = "Command not supported.\n" + USERNAME + "> "
                print(toSend, end="")

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