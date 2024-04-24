import socket

CENTRAL_SERVER_IP = '0.0.0.0'  # Listen on all available interfaces
CENTRAL_SERVER_PORT = 8008  # Port to listen on

STATS_LIST = {}


class Client:
    def __init__(self, username, address, port):
        self.username = username
        self.address = address
        self.port = port
        self.inGame = False
        self.invitesSentTo = []
        self.invitesFrom = []


def print_score_board(sock, client_address, added_message):
    sorted_players = sorted(STATS_LIST.items(), key=lambda x: x[1], reverse=True)
    # message = "Scoreboard: \n"
    message = r"""

┌─┐┌─┐┌─┐┬─┐┌─┐┌┐ ┌─┐┌─┐┬─┐┌┬┐
└─┐│  │ │├┬┘├┤ ├┴┐│ │├─┤├┬┘ ││
└─┘└─┘└─┘┴└─└─┘└─┘└─┘┴ ┴┴└──┴┘
------------------------------
"""
     
    for player, score in sorted_players:
        message += f"{player}: {score}\n"

    message += "\n" + added_message
    
    sock.sendto(message.encode(), client_address)



def clientMessage(message, client_address, sock):
    # gets the command/inoput from the client
    messageSplit = message.decode().split()
    command = messageSplit[0]
    # print("Command is:", command)

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

    # elif command == "who":
    #     num_users = 0
    #     theList = ""
    #     for client in clients:
    #         num_users += 1
    #         if client.inGame == True:
    #             status = "in game"
    #         else:
    #             status = "available"

    #         theList += f"{client.username} - {status}\n"
    #     # send completed list 
    #     message = "\nTotal " + str(num_users) + " users(s) online:\n"
    #     message += theList
    #     sock.sendto(message.encode(), client_address)

    elif command == "exit":
        print("tryig to exit")
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

    elif command == "score":

        num_users = 0
        theList = ""
        for client in clients:
            num_users += 1
            if client.inGame == True:
                status = "in game"
            else:
                status = "available"

            theList += f"{client.username} - {status}\n"
        # send completed list 
        message = "\nTotal " + str(num_users) + " users(s) online:\n"
        message += theList
        # sock.sendto(message.encode(), client_address)


        print_score_board(sock, client_address, message)
    
    elif command == "match":
        
        recipient_username = messageSplit[1] #gets the username of the recipient
        sender_username = messageSplit[2] #gets the username of the sender
        # print("should be sender username", sender_username)
        found = False
        playing = False
        #recipient for loop
        for client in clients:
            if client.username == recipient_username:
                if(client.inGame == True):
                    playing = True
                    break
                elif(client.inGame == False):
                    recipient = client
                    #adds the name of the sender to client's invites from list
                    #ensures no duplicates
                    if sender_username not in client.invitesFrom:
                        client.invitesFrom.append(sender_username) 

                    found = True
                    break
        #sender for loop
        for client in clients:
            if client.username == sender_username:
                #adds name of reciever to sendTo list
                #ensures no duplicates
                if recipient_username not in client.invitesSentTo:
                    client.invitesSentTo.append(recipient_username)

                #test code
                print("sender:", client.username)
                print("invites sent to:")
                for op in client.invitesSentTo:
                    print(op)            
    
                break

        if found:
            response = f"MATCH: {recipient.port}:{recipient.address}"
            sock.sendto(response.encode(), client_address)
        else:
            if(playing):
                sock.sendto(f"NO INFO: User {recipient_username} is in a game!".encode(), client_address)
            else:
                sock.sendto(f"NO INFO: User {recipient_username} is not online!".encode(), client_address)

    elif command == "decline":
        recipient_username = messageSplit[1] #gets the username of the recipient
        sender_username = messageSplit[2] #gets the username of the sender
        found = False
        error = False
        
        #recipient for loop
        for client in clients:
            if client.username == recipient_username:
                recipient = client
                #remove the person you invited to a game from the list
                try:
                    client.invitesSentTo.remove(sender_username)
                except ValueError:
                    print(f"{sender_username} not found!")
                    error = True
                
                if(error == False):
                    found = True

                break
        #sender for loop
        if(error == False):
            for client in clients:
                if client.username == sender_username:
                    #remove the other guy
                    try:
                        client.invitesFrom.remove(recipient_username)
                    except ValueError:
                        print("{sender_username} not found!")

                    break

        if found:
            response = f"DECLINE: {recipient.port}:{recipient.address}"
            sock.sendto(response.encode(), client_address)
        else:
            sock.sendto(f"NO INFO: User {recipient_username} has not sent you an invite!".encode(), client_address)

    elif command == "accept":
        recipient_username = messageSplit[1] #gets the username of the recipient
        sender_username = messageSplit[2] #gets the username of the sender
        #stores important connection info
        #thinking about having the server be the linker
        recipientAddress = -1
        recipientPort = -1
        senderAddress = -1
        senderPort = -1
        found = False
        error = False
        
        #recipient for loop
        for client in clients:
            if client.username == recipient_username:
                recipient = client
                #remove the person you invited to a game from the list
                try:
                    client.invitesSentTo.remove(sender_username)
                except ValueError:
                    print(f"{sender_username} not found!")
                    error = True
            
                if(error == False):
                    found = True
                    #set their in game status to true
                    client.inGame = True
                    #set addresses and ports
                    recipientAddress = client.address
                    recipientPort = client.port
                
                break
        if(error == False):
            #sender for loop
            for client in clients:
                if client.username == sender_username:
                    #remove the other guy
                    try:
                        client.invitesFrom.remove(recipient_username)
                    except ValueError:
                        print(f"{sender_username} not found!")
                    
                    #set their in game status to true
                    client.inGame =True
                    #set addresses and ports
                    senderAddress = client.address
                    senderPort = client.port

                    break

        if found:
            # send to sender 
            response = f"ACCEPT: {recipient.port}:{recipient.address}:{recipient.username}"
            sock.sendto(response.encode(), client_address)
            # send to reciever own info
            response = f"SERVER: {recipient.port}:{recipient.address}:{client.username}"
            sock.sendto(response.encode(), (recipient.address, recipient.port))
        
        else:
             sock.sendto(f"NO INFO: User {recipient_username} has not sent you an invite!".encode(), client_address)

    elif command == "shout":
        theList = "SHOUT\n"
        for client in clients:
            theList += f"{client.address}-{client.port}\n"
        # send completed list 
        sock.sendto(theList.encode(), client_address)

    elif command == "DRAW":
        user1 = messageSplit[1]
        user2 = messageSplit[2]

        for client in clients:
            if(client.username == user1 or client.username == user2):
                client.inGame = False
        
    elif command == "GAMEOVER":
        global STATS_LIST
        winner = messageSplit[1]
        loser = messageSplit[2]

        for client in clients:
            if(client.username == winner or client.username == loser):
                client.inGame = False
        
        if winner in STATS_LIST:
            STATS_LIST[winner] += 100  # Add points to existing player's score
        else:
            STATS_LIST[winner] = 100

        if loser not in STATS_LIST:
            STATS_LIST[loser] = 0
        
     

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