# Project-4-Parallel

# COP5570-Proj3

#####################################################
# Developed by Sophia Villalonga and Alejandro Ugas
# COP 5570 Concurrent, Parallel, and Distributed Programming 
# Florida State University Computer Science
#####################################################

Run the server:
python3 central.py

Then set up 2 users by using the command:
python3 peer.py <listening port>

Demo:

Command testing:

Test: ?
- enter the command: ?

<!-- 
score # List all online users
- assumung only user is logged in:
- run the command: who
    - you should only see one user: user
- login user1
- run the command: who
    - you should see both user and user1 
- have user1 quit
- run the command: who
    - you should only see one user: user

Test: stats [name] 
Log user1 back in.
- enter the command: stats
    - this will default to your personal stats: user's stats
- enter the command: stats user1
    - you will see user1's stats
- enter the command: stats user
    - this will show your personal stats: user's stats

Register user2 and user3.

game # list all current games
- enter the command: game
    - this will show there are 0 games

Test: match <name> <#|O> [t] # Try to start a game
As user:
- enter the command: match user1 # 600
- user1 will recieve: match user O 600
- As user1, paste the command into the prompt to start a game

game # list all current games
- enter the command: game
    - this will show there is 1 game

observe <game_num> # Observe a game
- As user2, use the output from the game command to observe <game_id>

<A|B|C><1|2|3> # Make a move in a game
- As user, enter any valid command: A1, A2, A3...

Both players(user and user1) and observers(user2) should see the move.

observe <game_num> # Observe a game
- As user3, use the output from the game command to observe <game_id>

kibitz <msg> # Comment on a game when observing
- As user3, enter the command: kibitz <msg>
- user2 will recieve the message

’ <msg> # Comment on a game
- As user2, enter the command: ’ <msg>
- user3 will recieve the message

refresh # Refresh a game
- As user2, enter the command: refresh
- This will print the gameboad back out
- As user or user1, enter the command: refresh
- This will print the gameboad back out

unobserve # Unobserve a game
- As user2, enter the command: unobserve
- As the game continues, user2 will not get updates

Play several games to show win/loss and draw conditions. 
Show stats will update wins and losses for the players. 

resign # Resign a game
- As a game player, enter the command: resign
- This will end the game and the player who resigned will lose. 

block <id> # No more communication from <id>
- enter the command: block <username>
- this will stop all communication from the username provided. 

unblock <id> # Allow communication from <id>
- enter the command: unblock <username>
- this will allow all communication from the username provided, if they were blocked prior. 

quiet # Quiet mode, no broadcast messages
- enter the command: quiet
- this will stop all broadcasted messages from arriving

nonquiet # Non-quiet mode
- enter the command: nonquiet
- this will allow all broadcasted messages to arrive

shout <msg> # shout <msg> to every one online
- Enter the command: shout <msg>
- this message will be delivered to everyone who is not quiet or blocked

tell <name> <msg> # tell user <name> message
- enter the command: tell <username> <msg>
- this message will be delivered only to the username provided unless you are blocked

mail <id> <title> # Send id a mail
- enter the command: mail <username> <title>
- then you will enter the body of the message. 
- this will send the mail to the provided username
- user and user1 have 1 mail each as an example

listmail # List the header of the mails
- enter the command: listmail
- this will list all mail recieved

readmail <msg_num> # Read the particular mail
- enter the command: readmail <msg_num>
- you can use the indexes given from listmail to read a specific mail

deletemail <msg_num> # Delete the particular mail
- enter the command: deletemail <msg_num>
- you can use the indexes given from listmail to delete a specific mail

info <msg> # change your information to <msg>
- enter the command: info <msg>
- enter stats to see the updated info

passwd <new> # change password
- enter the command: passwd <new_password>
- log out and log in with new password

exit # quit the system
- enter the command: exit
- if in an active game, this will end the game and you will lose
quit # quit the system
- enter the command: quit
- if in an active game, this will end the game and you will lose


Bugs: -->
