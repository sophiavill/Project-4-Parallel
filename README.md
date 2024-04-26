# Project-4-Parallel

# COP5570-Proj3

#####################################################
# Developed by Sophia Villalonga and Alejandro Ugas
# COP 5570 Concurrent, Parallel, and Distributed Programming 
# Florida State University Computer Science
#####################################################

Ensure the server and all peers are on the same linprog. 

Run the server:
python3 central.py

Then set up 2 users by using the command:
python3 peer.py <listening port>

Demo:

Command testing:
Provide a unique username uppon connecting. 

Test: ?
- enter the command: ?

score # List all online users and the current scoreboard 
- assumung both users are logged in:
- run the command: score
    - you should see both users
- login another user
- run the command: score
    - you should see three users
- have a user quit or have two users join a game
- run the command: score
    - you should see this reflect in game status or will remove the exited player

shout <msg> # shout <msg> to every one online
- Enter the command: shout <msg>
- this message will be delivered to everyone who is not actively in a game

tell <name> <msg> # tell user <name> message
- enter the command: tell <username> <msg>
- this message will be delivered only to the username provided unless they are in a game

Test: match <name> <game>  # Try to start a game
- the game options are:
    - ttt: tic tac toe
    - rps: rock paper scissors
    - bs: battle ship
- enter the command: match <usernamme> ttt

Test: accept <username>:
- after another user sends a match request:
- enter the command: accept <requester's username>
- this will start a game

Test: decline <username>:
- after another user sends a match request:
- enter the command: decline <requester's username>
- this will decline the game invitation and no game wil start


Now after accepting and starting a game:
- the peers in a game will display as "in game" from the central server


General game rules:
- it is assumed that all usere will play as intended
- users are able to commincate directley to the other player 
- a player can exit at any time 

These are in game commands:

tell  <msg>             # tell <message>
- enter the command: tell <message>
- send the other player a direct message 

exit                    # quit the system
enter the command: exit
- users will be brought back to the central server
- the user who quit will lose the game and the other player will win

refresh                 # print the game board
- enter the command: refresh 
- for each game individaully, this will re-display the game board or game command

?                       # print this message
- enter the command: ?
- this will print out all game menu items


Inside of a tictactoe game:
- the X's and O's are randomly assigned and X goes first
- to play a piece enter the row: (A, B or C) then enter the column: (1, 2, or 3):
    - example: A1 or B3... 

- for a draw, both users will return to the central server
- their status will change to avaiable 
- no points will be rewarded for a draw

- for a successful game both players will be put back into the central server
- the winner will recieve 100 points and the loser 0


Inside of a rock, paper, scissors game:
- the game is best 2/3
- if there is a draw between moves, the players will play again
- once a player wins both players will be put back into the central server
- the winner will recieve 100 points and the loser 0

- enter rock, paper, scissors, Rock, Paper, or Scissors


Inside of a battle ship
- the X's represent dropped bombs
- O's are the user's own ships
- #'s are sunken other player's ships

First you will be prompted to place your own two ships
- to place ships or drop bomb enter the row: (1-5) then enter the column: (A-E):
    - example: 1A or 3B... 
