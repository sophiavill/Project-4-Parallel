import socket
import threading
import queue
import sys
import select
import time
import random

# central server info
CENTRAL_SERVER_IP = '0.0.0.0' 
#CENTRAL_SERVER_IP = '128.186.120.158' 
CENTRAL_SERVER_PORT = 8008

# bool to know when to exit
EXIT_NOW = False
# holds the clients username and states 
USERNAME = ""
IN_GAME = False
IS_SERVER = False
IS_CLIENT = False

# holds client/socket info
CLIENT_SOCKET = 0
SOC_LIST = []
SERVER_SOCKET = 0
SOCK = None
READABLE = None
CURRENT_GAME = None

currentMessage = ""

# global game info
game_list = "ttt" , "rps", "bs"
GAME_TYPE = ""

class RPSGame():
    def __init__(self):
        self.player1_name = " "
        self.player2_name = " "
        self.player1_move = ""
        self.player2_move = ""
        self.player1_score = 0
        self.player2_score = 0
        self.winner = ""
        self.loser = ""

class BSGame():
    def __init__(self):
        self.player1_name = " "
        self.player2_name = " "
        # self.player1_move = ""
        # self.player2_move = ""
        self.player1_score = 0
        self.player2_score = 0
        self.winner = ""
        self.loser = ""
        self.waiting_for_ship_client = True
        self.waiting_for_ship_server = True
        # 2 boards each player: one for their own ships/board, one for their attempts 
        self.player1_my_board = self.init_board()
        self.player1_other_board = self.init_board()
        self.player2_my_board = self.init_board()
        self.player2_other_board = self.init_board()
    
    def init_board(self):
        return [['.' for _ in range(5)] for _ in range(5)]

class Game:
    def __init__(self):
        self.player1_name = " "
        self.player2_name = " "
        self.board = self.init_board()
        # faction is X or O
        self.player1_faction = " "
        self.player2_faction = " "
        self.current_player = ""
        self.played_moves = [False] * 9
        self.player_spot = [" "] * 9
        self.winner = ""
        self.loser = ""
        self.draw = False

    def init_board(self):
        return [['.' for _ in range(3)] for _ in range(3)]
    
#----------------------------------------------------------------------------------------------------------------

def rpsCheck(game):
    global CURRENT_GAME
    thewinner = ""
    over = False
    rock = '''  
        I===++*+**+
    I===++*+**+=*+=*+
    I=+++++=++++****+=
    I=++++====+++++=*+=
    I+++=+==+=++=+++++
    I=====+++++++=-*
        I=+=++++++++=
        '''

    paper = '''  
    I==========I
    I==========I
    I==========I
    I==========I
    I==========I
    I==========I
    I==========I
        '''

    scissors = r'''  
    _       ,/'
   (_).  ,/'
   __  ::
  (__)'  `\.
            `\.
 
        ''' 

    # draw
    if game.player1_move == game.player2_move:
        message = "\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
        message += "\nIt's a tie! Play again."
        message += "\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        message += f"\n\n{game.player1_name}: {game.player1_score}\t\t{game.player2_name}: {game.player2_score}"
        message += "\nEnter Rock, Paper, or Scissors!\n"
        print_client_side(message)
    
        message += f"{USERNAME}> "
        print(message, end = "")
        # reset move variables 
        CURRENT_GAME.player1_move = ""
        CURRENT_GAME.player2_move = ""
        return

    elif (game.player1_move == 'Rock' and game.player2_move == 'Scissors') or \
         (game.player1_move == 'Paper' and game.player2_move == 'Rock') or \
         (game.player1_move == 'Scissors' and game.player2_move == 'Paper'):
        # player 1 wins
        CURRENT_GAME.player1_score += 1
        thewinner = CURRENT_GAME.player1_name
        win_move = game.player1_move
        loss_move = game.player2_move
    else:
        # player 2 wins
        CURRENT_GAME.player2_score += 1
        thewinner = CURRENT_GAME.player2_name
        win_move = game.player2_move
        loss_move = game.player1_move
    # get the ascii art in
    if(win_move == "Rock"):
        win_move = rock 
    elif(win_move == "Paper"):
        win_move = paper 
    elif(win_move == "Scissors"):
        win_move = scissors 
    
    if(loss_move == "Rock"):
        loss_move = rock 
    elif(loss_move == "Paper"):
        loss_move = paper 
    elif(loss_move == "Scissors"):
        loss_move = scissors

    # game is over
    if(CURRENT_GAME.player1_score != 2 and CURRENT_GAME.player2_score != 2):
        message = "\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
        message += f"\n{thewinner} wins this round! On to the next game"
        message += f"\n\n{win_move} \nbeats\n {loss_move}"
        message += "\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        message += f"\n\n{game.player1_name}: {game.player1_score}\t\t{game.player2_name}: {game.player2_score}"
        message += "\nEnter Rock, Paper, or Scissors!\n"
    
    else:
        if (CURRENT_GAME.player1_score == 2):
            # player 1 wins it all
            CURRENT_GAME.winner = CURRENT_GAME.player1_name
            win_move = CURRENT_GAME.player1_move
            CURRENT_GAME.loser = CURRENT_GAME.player2_name
            loss_move = CURRENT_GAME.player2_move
        else:
            # player 2 wins it all
            CURRENT_GAME.winner = CURRENT_GAME.player2_name
            win_move = CURRENT_GAME.player2_move
            CURRENT_GAME.loser = CURRENT_GAME.player1_name
            loss_move = CURRENT_GAME.player1_move
        
        if(win_move == "Rock"):
            win_move = rock 
        elif(win_move == "Paper"):
            win_move = paper 
        elif(win_move == "Scissors"):
            win_move = scissors 
        
        if(loss_move == "Rock"):
            loss_move = rock 
        elif(loss_move == "Paper"):
            loss_move = paper 
        elif(loss_move == "Scissors"):
            loss_move = scissors

        message = f"\n\n{thewinner} wins this round! \n\n{win_move} \nbeats\n {loss_move} \n\nGAME OVER!! \nWinner is: {CURRENT_GAME.winner}, Loser is: {CURRENT_GAME.loser}\n\n"
        over = True
        
    print_client_side(message)
    message += f"{USERNAME}> "
    print(message, end = "")
    
    # end the game
    if over == True:
        print_client_side('EXIT_NOW')
    
    # reset move variables every round
    CURRENT_GAME.player1_move = ""
    CURRENT_GAME.player2_move = ""

# print client side from game server
def print_client_side(message):
    for sock in SOC_LIST:
        if sock != SERVER_SOCKET and sock != sys.stdin:
            sock.sendall(message.encode())

# print the board only for ttt and rps - used for refresh as well
def print_board(current_game, name):
    if GAME_TYPE == "ttt":
        board_str = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
        board_str += f"\n\n{current_game.current_player}'s turn!"
        board_str += f"\n{current_game.player1_name}: {current_game.player1_faction} \t\t {current_game.player2_name}: {current_game.player2_faction}\n"
        board_str += "\n    1  2  3\n"
        for i in range(3):
            row_label = chr(ord('A') + i)
            board_str += row_label + "  "
            for j in range(3):
                board_str += " " + current_game.board[i][j] + " "
            board_str += "\n"
    
    elif GAME_TYPE == "rps":
        board_str = f"\n\n{current_game.player1_name}: {current_game.player1_score}\t\t{current_game.player2_name}: {current_game.player2_score}"
        board_str += "\nEnter Rock, Paper, or Scissors!\n"

    if(name == "server"):
        print(board_str + "\n"+ USERNAME + ">", end="")
    else:
        print_client_side(board_str)

# use for bs - used for refresh as well
def print_board_bs(board, name, checkHere):
    board_str = ""
    if checkHere == True:
        board_str = "\nHere is your board. O represents your ships, X is a hit: "
    else:
        board_str = "\nHere is your opponent's board. # represents HIT ships, X is miss: "

    board_str += "\n    A  B  C  D  E\n"
    for i in range(5):
        row_label = 1 + i
        board_str += str(row_label) + "  "
        for j in range(5):
            board_str += " " + board[i][j] + " "
        board_str += "\n"

    if(name == "server"):
        print(board_str + "\n"+ USERNAME + ">", end="")
    else:
        print_client_side(board_str)

# check for winner in ttt
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
   # if anything is empty, there is no draw
   for i in range(3):
       for j in range(3):
           if board[i][j] == '.':
               return False 
    # if all spots full, draw
   return True 

# actual playing of ttt
def gameplay(move, player_type, faction):
    global CURRENT_GAME

    row, col = move[0], int(move[1]) - 1
    row_index = ord(row) - ord('A')
    column_index = col

    # error check
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

    # print board to both players after a move is made
    print_board(CURRENT_GAME, "server")
    print_board(CURRENT_GAME, "client")

    # if there is a win, see who won
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
        # exit if win
        print_client_side('EXIT_NOW')
    
    elif(check_draw(CURRENT_GAME.board)):
        message = "Game over! Its a draw!\n"
        print(message)
        print_client_side(message)
        CURRENT_GAME.draw = True
        # exit if draw
        print_client_side('EXIT_NOW')

# end of game funcs-------------------------------------------------------------------------
def exitFuncServer(source):
    # exit from the game server back to the central server
    SOC_LIST.remove(source)
    source.close()
    SERVER_SOCKET.close()
    global IN_GAME, IS_SERVER
    IN_GAME = False
    IS_SERVER = False
    print(f"Welcome back to the game server!")
    # tell the client to exit too
    print_client_side('GAMEOVER')

    print("here in exit. WInner is: ", CURRENT_GAME.winner, " loser is: ", CURRENT_GAME.loser)

    #tell the central server - all games (except in a draw case) return the same way
    if(GAME_TYPE == "ttt"):
        if(CURRENT_GAME.draw):
            message = f"DRAW {CURRENT_GAME.player1_name} {CURRENT_GAME.player2_name}".encode()
        else:
            message = f"GAMEOVER {CURRENT_GAME.winner} {CURRENT_GAME.loser}".encode()
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
            
                messageToSend = f"\nDo you want to accept the game from {USERNAME}?\n(accept {USERNAME} or decline {USERNAME})"
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
                # since they are both starting and connecting at the same time,
                # the user may need a delay in connecting to the server
                # they will try 5 times to connect with a growing delay 
                for attempt in range(retries):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((address, port))
                        break 
                    except ConnectionRefusedError:
                        print(f"Trying to connect to game...")
                        time.sleep(delay) 

                if not sock:
                    raise Exception("Could not connect to server. Request game again.")
                    return
                
                print("\nSuccess! Game started with:", other_player_name)
                print_game_menu(1)

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
                        # Use select to handle input from multiple sockets
                        readable, _, _ = select.select(sockets_list, [], [])
                        global READABLE
                        READABLE = readable
                        for source in readable:
                            if source == server_socket:
                                client_socket, client_address = server_socket.accept()
                                sockets_list.append(client_socket)
        
                                if(printedBool == False):
                                    # print this welcome the first time they connect
                                    if GAME_TYPE == 'ttt':
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

                                    if GAME_TYPE == "rps":
                                        current_game = RPSGame()
                                        print("\nSuccess! Game started with:", other_player_name)

                                        # get the server the game menu
                                        print_game_menu(1)

                                        message = "Welcome to Rock, Paper, Scissors: \n"
                                        message += "Each player will input their move. Best 2/3 wins!\n\n"
                                        
                                        current_game.player1_name = USERNAME
                                        current_game.player2_name = other_player_name

                                        message += f"{current_game.player1_name}: {current_game.player1_score}\t\t{current_game.player2_name}: {current_game.player2_score}"

                                        message += "\nEnter Rock, Paper, or Scissors!\n"
                                        print_client_side(message)
                                        message += f"{USERNAME}> "
                                        print(message, end="")

                                        printedBool = True
                                        CURRENT_GAME = current_game
                                    
                                    if GAME_TYPE == "bs":
                                        current_game = BSGame()
                                        print("\nSuccess! Game started with:", other_player_name)

                                        current_game.player1_name = USERNAME
                                        current_game.player2_name = other_player_name

                                        # get the server the game menu
                                        print_game_menu(1)

                                        message = "Welcome to Battle Ship!: \n"
                                        message += "Each player will input the location of their 2 ships. Sink enemy ships to win!\n\n"

                                        print_board_bs(current_game.player1_my_board, "server", True)
                                        print_board_bs(current_game.player2_my_board, "client", True)

                                        message += "Enter the location of your two ships (ex: 1A 3B)!\n\n"

                                        print_client_side(message)
                                        message += f"{USERNAME}> "
                                        print(message, end="")

                                        printedBool = True
                                        CURRENT_GAME = current_game

                            else:
                                # handle client socket
                                data = source.recv(1024)
                                clean_data = data.decode().strip()
                                commandSplit = clean_data.split()
                                # split command and other following inputs
                                if commandSplit:
                                    command = commandSplit[0]
                                else:
                                    command = " "
                                
                                if data:
                                    if(command == "exit"):
                                        if(CURRENT_GAME.winner == ""):
                                            CURRENT_GAME.winner = CURRENT_GAME.player1_name
                                            CURRENT_GAME.loser = CURRENT_GAME.player2_name

                                        # exit the game server
                                        exitFuncServer(source)

                                    if GAME_TYPE == "ttt":
                                        if command == "MOVE":
                                            # check if their turn
                                            if(CURRENT_GAME.current_player != USERNAME):
                                                gameplay(commandSplit[1], "client", CURRENT_GAME.player2_faction)
                                            else:
                                                print_client_side("It is not your turn!")
                                            
                                        elif(command == "refresh"):
                                            print_board(CURRENT_GAME, "client")
                                            
                                        else:
                                            clean_send = clean_data + "\n" + USERNAME + "> "
                                            print(clean_send, end="")

                                    elif GAME_TYPE == "rps":
                                        if(command == "MOVE"):
                                            # assign the choice 
                                            CURRENT_GAME.player2_move = commandSplit[1]
                                            # check if other person played 
                                            if CURRENT_GAME.player1_move != "":
                                                # check for a win
                                                rpsCheck(CURRENT_GAME)
                                            else:
                                                print_client_side(f"Waiting for {CURRENT_GAME.player1_name}...")
                                        elif(command == "refresh"):
                                            print_board(CURRENT_GAME, "client")
                                        else:
                                            clean_send = clean_data + "\n" + USERNAME + "> "
                                            print(clean_send, end="")
                                    
                                    elif GAME_TYPE == "bs":
                                        if(CURRENT_GAME.waiting_for_ship_client == True):
                                            # get location of their own ships
                                            if command == "MOVE":
                                                if len(commandSplit) == 3:
                                                    # ship 1
                                                    move = commandSplit[1]

                                                    row, col = int(move[:-1]), move[-1]  
                                                    row_index = row - 1
                                                    column_index = ord(col) - ord('A')

                                                    CURRENT_GAME.player2_my_board[row_index][column_index] = "O"
                                                    
                                                    # ship 1
                                                    move = commandSplit[2]
                                                    
                                                    row, col = int(move[:-1]), move[-1]
                                                    row_index = row - 1
                                                    column_index = ord(col) - ord('A')

                                                    CURRENT_GAME.player2_my_board[row_index][column_index] = "O"

                                                    # add ships to board
                                                    print_board_bs(current_game.player2_my_board, "client", True)
                                                    CURRENT_GAME.waiting_for_ship_client = False
                                                    print_client_side("\n\nEnter target coordinate: ")
                                                else:
                                                    print_client_side("\nMissing a ship.")

                                            elif(command == "refresh"):
                                                print_board_bs(CURRENT_GAME.player2_my_board, "client", True)
                                                print_board_bs(CURRENT_GAME.player2_other_board, "client", False)
                                            else:
                                                print_client_side("\nEnter ships first.")
                                            
                                        elif(command == "MOVE" and CURRENT_GAME.waiting_for_ship_client == False):
                                            # getting regular coordinate iput from client (player 2)
                                            move = commandSplit[1]

                                            row, col = int(move[:-1]), move[-1]
                                            row_index = row - 1
                                            column_index = ord(col) - ord('A')
                                            # if the spot was blank (no hit)
                                            if (CURRENT_GAME.player1_my_board[row_index][column_index] == '.'):
                                                # put an X on both my board and the other player board to show
                                                # where I dropped my bomb
                                                CURRENT_GAME.player1_my_board[row_index][column_index] = "X"
                                                CURRENT_GAME.player2_other_board[row_index][column_index] = "X"
                                                print_board_bs(CURRENT_GAME.player2_my_board, "client", True)
                                                print_board_bs(CURRENT_GAME.player2_other_board, "client", False)
                                                print_client_side("No hit! \n\nEnter target coordinate:")
                                            
                                            # if the spot had a ship in it (hit!)
                                            elif (CURRENT_GAME.player1_my_board[row_index][column_index] == 'O'):
                                                # put an # on both my board and the other player board to show
                                                # where the ship sank
                                                CURRENT_GAME.player1_my_board[row_index][column_index] = "#"
                                                CURRENT_GAME.player2_other_board[row_index][column_index] = "#"
                                                print_board_bs(CURRENT_GAME.player2_my_board, "client", True)
                                                print_board_bs(CURRENT_GAME.player2_other_board, "client", False)

                                                CURRENT_GAME.player2_score += 1
                                                messageHere = "Nice hit, you sunk a ship!"
                                                # if they sunk both ships
                                                if(CURRENT_GAME.player2_score == 2):
                                                    CURRENT_GAME.winner = CURRENT_GAME.player2_name
                                                    CURRENT_GAME.loser = CURRENT_GAME.player1_name
                                                    message_here = f"\nGood job! You sunk all of {CURRENT_GAME.player1_name}'s ships! You win!"
                                                    print_client_side(message_here)
                                                    message_here = f"\nYou lose! {CURRENT_GAME.player2_name} sunk all of your ships!"
                                                    print(message_here)
                                                    exitFuncServer(source)
                                                        
                                                else:
                                                    messageHere += "\n\nEnter target coordinate:"
                                                
                                                print_client_side(messageHere)
                                           
                                            # already dropped a bomb there 
                                            elif (CURRENT_GAME.player1_my_board[row_index][column_index] == 'X'):
                                                print_client_side("You already hit this spot! \n\nEnter target coordinate:")
                                        
                                        # print both boards again
                                        elif(command == "refresh"):
                                            print_board_bs(CURRENT_GAME.player2_my_board, "client", True)
                                            print_board_bs(CURRENT_GAME.player2_other_board, "client", False)

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
                # the central server will send all users IP addresses sep by newlines
                lines = message.split('\n')
                for line in lines[1:]:
                    lineSplit = line.split('-')
                    # sep each line and take the address and port for each player 
                    if len(lineSplit) >= 2:
                        address = lineSplit[0]
                        port = int(lineSplit[1])
                        finalMessage = f"*{USERNAME}*: " + currentMessage
                        sock.sendto(finalMessage.encode(), (address, port))
                print("Message sent.\n" + USERNAME + "> ", end="")
            
            elif message.startswith("GAMEOVER"):
                # come back from game server
                print(f"Welcome back to the game server!")
                IN_GAME = False
                IS_CLIENT = False
                message_queue = queue.Queue()
                threading.Thread(target=receiveMessages, args=(SOCK, message_queue), daemon=True).start()
                user_interface(SOCK, listen_port, message_queue)
                SOCK.close()
            
            # signal to the game server we want to exit 
            elif message.startswith("EXIT_NOW"):
                command = "exit"
                CLIENT_SOCKET.sendall(command.encode())
    
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


# all these are sent to/communicated with central server
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
                    
                         █████╗ ██████╗  ██████╗ █████╗ ██████╗ ███████╗
                        ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝
                        ███████║██████╔╝██║     ███████║██║  ██║█████╗  
                        ██╔══██║██╔══██╗██║     ██╔══██║██║  ██║██╔══╝  
                        ██║  ██║██║  ██║╚██████╗██║  ██║██████╔╝███████╗
                        ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝
                                                                
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        """
    print("\n\n\t\t" + tic + "\n")

    username = input("> Enter your username: ")
    # save username as a global variable for easy access
    global USERNAME 
    USERNAME = username

    message = f"register {own_port} {username}".encode()
    sock.sendto(message, (CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT))

# all sent to central server
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
    # ensures server has the username of the recipient, message, lisitening port, and username of sender
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
    print("May need to enter to confirm > ", end="")

    global EXIT_NOW
    EXIT_NOW = True
    while EXIT_NOW:
        sys.exit(0)

def print_menu():
    print("\nMenu:")
    print("  shout <msg>             # shout <msg> to every one online")
    print("  tell <name> <msg>       # tell user <name> message")
    print("  exit                    # quit the system")
    print("  match <name> <game>     # Try to start a game (ttt, rps, bs)")
    print("  accept <name>           # Accept an invite")
    print("  decline <name>          # Decline an invite")
    print("  score                   # Print the scoreboard and user availability")
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

# take input in from user
def user_interface(sock, listen_port, message_queue):
    threading.Thread(target=printMessage, args=(message_queue,), daemon=True).start()
    # first time, print menu
    print_menu()
    
    while True:
        # break up input if needed
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
        global GAME_TYPE

        if(IN_GAME == True):
            valid_moves = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
            rps_moves = ["Rock", "Paper", "Scissors", "rock", "paper", "scissors"]
            bs_moves = ['1A', '2A', '3A', '4A', '5A', '1B', '2B', '3B', '4B', '5B', '1C', '2C', '3C', '4C', '5C', '1D', '2D', '3D', '4D', '5D', '1E', '2E', '3E', '4E', '5E']

            # client in peer to peer server
            if(IS_CLIENT == True):
                message = allCommand
                if command == "tell":
                    message = f"\n{USERNAME}: {' '.join(commandSplit[1:])}"
                    CLIENT_SOCKET.sendall(message.encode())
                    print(USERNAME + "> ", end="")
                elif(command == "?"):
                    print_game_menu(2)
                elif(command == "exit"):
                    CLIENT_SOCKET.sendall(command.encode())
                # valid ttt moves
                elif(command in valid_moves):
                    message = f"MOVE {command}"
                    CLIENT_SOCKET.sendall(message.encode())
                elif(command == "refresh"):
                    CLIENT_SOCKET.sendall(command.encode())
                # valid rps moves
                elif command in rps_moves:
                    command = command.lower().capitalize()
                    message = f"MOVE {command}"
                    CLIENT_SOCKET.sendall(message.encode())
                # valid bs moves
                elif command in bs_moves:
                    # if its the first two ship placements
                    if len(commandSplit) == 2:
                        if(command in bs_moves and commandSplit[1] in bs_moves):
                            message = f"MOVE {command} {commandSplit[1]}"
                        else:
                            print_client_side("Invalid input. Try again. ")
                    
                    # just regular gameplay
                    else:
                        message = f"MOVE {command}"
                    
                    CLIENT_SOCKET.sendall(message.encode())

                else:
                    toSend = "Command not supported.\n" + USERNAME + "> "
                    print(toSend, end="")
            
             # server in peer to peer server
            if(IS_SERVER == True):
                # server directly handles peer input from the peer who is the server  
                if(command == "tell"):
                    message = f"\n{USERNAME}: {' '.join(commandSplit[1:])}"
                    print_client_side(message)
                    print(USERNAME + "> ", end="")
                elif(command == "?"):
                    print_game_menu(2)
                elif(command == "refresh"):
                    if (GAME_TYPE == "ttt" or GAME_TYPE == "rps"):
                        print_board(CURRENT_GAME, "server")
                    elif(GAME_TYPE == "bs"):
                        print_board_bs(CURRENT_GAME.player1_my_board, "server", True)
                        print_board_bs(CURRENT_GAME.player1_other_board, "server", False)
                         
                elif(command == "exit"):
                    CURRENT_GAME.winner = CURRENT_GAME.player2_name
                    CURRENT_GAME.loser = CURRENT_GAME.player1_name
                    # all exiting has to happen inside server loop
                    print_client_side('EXIT_NOW')
                
                elif(command in valid_moves and GAME_TYPE == "ttt"):
                    # check if my turn, do stuff based on that
                    if(CURRENT_GAME.current_player == USERNAME):
                        gameplay(command, "server", CURRENT_GAME.player1_faction)     
                    else:
                        print("It is not your turn!\n" + USERNAME + "> ", end="")

                elif (command in rps_moves):
                        command = command.lower().capitalize()
                        print("Command from the server: ", command)
                       # assign the choice 
                        CURRENT_GAME.player1_move = command
                        # check if other person played 
                        if CURRENT_GAME.player2_move != "":
                            # check for a win
                            rpsCheck(CURRENT_GAME)
                        else:
                            toSend = f"Waiting for {CURRENT_GAME.player2_name}... \n{USERNAME}> "
                            print(toSend, end="")
                
                elif (command in bs_moves and GAME_TYPE == "bs"):
                    if(CURRENT_GAME.waiting_for_ship_server == True):
                        if(len(commandSplit) == 2):
                            if(commandSplit[0] in bs_moves):
                                # same code as in server section
                                move = commandSplit[0]

                                row, col = int(move[:-1]), move[-1]
                                row_index = row - 1
                                column_index = ord(col) - ord('A')

                                CURRENT_GAME.player1_my_board[row_index][column_index] = "O"

                                move = commandSplit[1]
                                
                                row, col = int(move[:-1]), move[-1]
                                row_index = row - 1
                                column_index = ord(col) - ord('A')

                                CURRENT_GAME.player1_my_board[row_index][column_index] = "O"

                                # add ships to board
                                print_board_bs(CURRENT_GAME.player1_my_board, "server", True)
                                toSend = "\n\nEnter target coordiante: \n" + USERNAME + "> "
                                print(toSend, end="")
                                CURRENT_GAME.waiting_for_ship_server = False
                            else:
                                toSend = "\n\nMissing a ship!  \n" + USERNAME + "> "
                                print(toSend, end="")
                        else:
                            toSend = "\n\nMissing a ship!  \n" + USERNAME + "> "
                            print(toSend, end="")
                    
                    else:
                        # same code as in server section
                        move = commandSplit[0]
                        row, col = int(move[:-1]), move[-1]
                        row_index = row - 1
                        column_index = ord(col) - ord('A')

                        if (CURRENT_GAME.player2_my_board[row_index][column_index] == '.'):
                            CURRENT_GAME.player2_my_board[row_index][column_index] = "X"
                            CURRENT_GAME.player1_other_board[row_index][column_index] = "X"
                            print_board_bs(CURRENT_GAME.player1_my_board, "server", True)
                            print_board_bs(CURRENT_GAME.player1_other_board, "server", False)
                            print("No hit! \n\nEnter target coordinate:")
                        
                        elif (CURRENT_GAME.player2_my_board[row_index][column_index] == 'O'):
                            
                            CURRENT_GAME.player2_my_board[row_index][column_index] = "#"
                            CURRENT_GAME.player1_other_board[row_index][column_index] = "#"
                            print_board_bs(CURRENT_GAME.player1_my_board, "server", True)
                            print_board_bs(CURRENT_GAME.player1_other_board, "server", False)

                            CURRENT_GAME.player1_score += 1
                            messageHere = "Nice hit, you sunk a ship!"

                            if(CURRENT_GAME.player1_score == 2):
                                CURRENT_GAME.winner = CURRENT_GAME.player1_name
                                CURRENT_GAME.loser = CURRENT_GAME.player2_name
                                message_here = f"\nGood job! You sunk all of {CURRENT_GAME.player2_name}'s ships! You win!\n"
                                print(message_here)
                                message_here = f"\nYou lose! {CURRENT_GAME.player1_name} sunk all of your ships!"
                                print_client_side(message_here)
                                print_client_side('EXIT_NOW')   
                                    
                            else:
                                messageHere += "\n\nEnter target coordinate:"
                            
                            print(messageHere)
                        
                        elif (CURRENT_GAME.player1_my_board[row_index][column_index] == 'X'):
                            print("You already hit this spot! \n\nEnter target coordinate:")
                    
                else:
                    toSend = "Command not supported.\n" + USERNAME + "> "
                    print(toSend, end="")

#--------------------------------------------------------------------------------------------------------------------------------------
# regular server functions
                            
        else:
            if command == "score":
                scoreCommand(sock)

            elif command == "shout":
                # collect the message and request all users info
                if len(commandSplit) >= 2:
                    message = ' '.join(commandSplit[1:])
                    global currentMessage
                    currentMessage = message
                    shoutCommand(sock)
                else:
                    print("Missing message")
                    print(USERNAME + "> ", end="")
            # very similar to shout, just individual
            elif command == "tell":
                if len(commandSplit) >= 3:
                    commandSplit = allCommand.split(" ", 2)
                    recipient = commandSplit[1] 
                    message = commandSplit[2] 
                    currentMessage = message
                    tellCommand(recipient, sock, listen_port)
                else:
                    print("Missing user or message")
                    print(USERNAME + "> ", end="")
            # triggers exit func
            elif command == "exit":
                message_queue.put("exit")
                exitCommand(SOCK, listen_port)
                break
            
            elif command == "?":
                print_menu()
            # send match request to server to get needed info to send to user
            elif command == "match":
                if len(commandSplit) >= 3:
                    game_type = commandSplit[2]
                    if game_type not in game_list:
                        print("Game type not valid.")
                        print(USERNAME + "> ", end="")
    
                    else:  
                        player2 = commandSplit[1]
                        message = f"match invite from:{USERNAME}:{socket.gethostbyname(socket.gethostname())}:{listen_port}"
                
                        matchCommand(message, player2, sock, listen_port)
                        currentMessage = message
                        # assign the game type as a global varible
                        GAME_TYPE = game_type
                    
                else:
                    print("Missing recipient username or game type.")
                    print(USERNAME + "> ", end="")
            # tells server about the decline
            elif command == "decline":
                if len(commandSplit) >= 2:
                    player2 = commandSplit[1]
                    message = f"{USERNAME} has declined your invite!"
                    
                    declineCommand(message, player2, sock, listen_port)
                    currentMessage = message
            
                else:
                    print("Missing recipient username.")
                    print(USERNAME + "> ", end="")
            # tells server about the accept, also will trigger to start server
            elif command == "accept":
                if len(commandSplit) >= 2:
                    player2 = commandSplit[1]
                    message = f"{USERNAME} has accepted your invite!"

                    acceptCommand(message, player2, sock, listen_port)
                    currentMessage = message

                else:
                    print("Missing recipient username.")
                    print(USERNAME + "> ", end="")
      
            else:
                toSend = "Command not supported.\n" + USERNAME + "> "
                print(toSend, end="")

def main(listen_port):
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
        print("Usage: python3 peer.py <listening port>")
        sys.exit(1)
    listen_port = int(sys.argv[1])
    main(listen_port)
