#define _POSIX_SOURCE
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <sys/select.h>
#include <algorithm>
#include <iostream>
#include <cstring>
#include <string>
#include <string.h>
#include <strings.h>
#include <cctype>
#include <fstream>
#include <sstream>
#include <csignal>
#include <unordered_set>
#include <sys/time.h>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <iomanip>
#include <chrono>

using namespace std;
using namespace chrono;

// count total of num users online 
int NUM_USERS = 0;

// max users online
int MAXCONN = 20;

// struct for client array
struct clientInfo {
	int socket;
    string username = " ";
	string command = " ";
    string rest = " ";
	int counter = 0;

	// states 
    bool welcomeChoice = false;
	bool waitingForCommand = false;
};

void printUserNameLine(clientInfo client[], int i, string username, int socket){
	string message = "<" + username + ": " + to_string(client[i].counter) + " > ";
	const char* msg = message.c_str();
	write(socket, msg, strlen(msg));
	//increments the counter
	client[i].counter += 1;
}

void rtrim(char *s) {
	//get the length of the string
	int length = strlen(s);
	//while loop used to trim ant extra characters
	while (length > 0 && isspace(s[length - 1])) {
			s[length - 1] = '\0';
			length--;
	}
}

string ltrim(string str) {
	//see if the start is any whitespace character
    size_t start = str.find_first_not_of(" \n\r\t\f\v");
	//return the string without extra front whitespace
    return (start == string::npos) ? "" : str.substr(start);
}

//used to trim the whitespace in the beginning of the password entered
string trimLeft(string& str) {
	
	str.erase(remove_if(str.begin(), str.end(), ::isspace),str.end());
	return str;
	
}

void printNotice(int cli_sockfd) {
    const char* welcomeMsg =  "            -=-= AUTHORIZED USERS ONLY =-=-\n"
                              "You are attempting to log into online tic-tac-toe Server.\n"
                              "Please be advised by continuing that you agree to the terms of the\n"
                              "Computer Access and Usage Policy of online tic-tac-toe Server.\n";
	send(cli_sockfd, welcomeMsg, strlen(welcomeMsg), 0);
    //write(cli_sockfd, welcomeMsg, strlen(welcomeMsg));
}

void printWelcome(int cli_sockfd){
	const char* welcome = 
		"\n\n\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
		"\t\t%                                         %\n"
		"\t\t%              Welcome to P2P             %\n"
		"\t\t%            Online Tic-tac-toe           %\n"
		"\t\t%                                         %\n"
		"\t\t%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
		"\nWelcome! Enter a username: ";
	send(cli_sockfd, welcome, strlen(welcome), 0);
}

void printHelp(clientInfo client[], int i){
	const char* helpMenu =  
    "\n"
	"  who                     # List all online users\n"
	"  stats [name]            # Display user information\n"
	"  shout <msg>             # shout <msg> to every one online\n"
	"  tell <name> <msg>       # tell user <name> message\n"
	"  exit                    # quit the system\n"
	"  quit                    # quit the system\n"
	"  help                    # print this message\n"
	"  ?                       # print this message\n";
	// username line
	write(client[i].socket, helpMenu, strlen(helpMenu));
}

void welcomeChoiceFunc(clientInfo client[], int i){
	bool active = false;
	for(int k = 0; k < NUM_USERS; k++){
		if(client[i].command == client[k].username){
			const char* msg = "That username is already logged in. Try again. \n";
			write(client[i].socket, msg, strlen(msg));
			msg = "Enter your username: ";
			write(client[i].socket, msg, strlen(msg));
			active = true;
		}
	}
	if(!active){
		// make that thier username 
		client[i].username = client[i].command;
		client[i].welcomeChoice = false;
		client[i].waitingForCommand = true;
		NUM_USERS++;
		//printWelcome(client[i].socket);
		string msg = "\nWelcome to the waiting room, " + client[i].username + "!\n";
		const char* msg2 = msg.c_str();
		write(client[i].socket, msg2, strlen(msg2));
		//printHelp(client, i);
		//printUserNameLine(client, i, client[i].username, client[i].socket);
	}
}

void who(clientInfo client[], int i){
	string msg = "\nTotal " + to_string(NUM_USERS) + " users(s) online:\n";
	for (int j=0; j<MAXCONN; j++) {
			if (client[j].socket < 0) continue;
		msg += client[j].username + "\n";
	}
	msg += "\n";

	const char* msg2 = msg.c_str();
	write(client[i].socket, msg2, strlen(msg2));
}

void shout(clientInfo client[], int i){
	//takes in and cleans up the message
    string message = client[i].rest;
    message = ltrim(message);
    //sets up the header
    string header = "!shout! *";
    header += client[i].username;
    header += "*: ";
    message = header + message + "\n";
    const char* msg = message.c_str();
             
    //loops through all active sockets and shouts
    for (int j=0; j<MAXCONN; j++) {
		write(client[j].socket, msg, strlen(msg));
		if(j != i)
			printUserNameLine(client, j, client[j].username, client[j].socket);
	}
		
}

void tell(clientInfo client[], int i){
	//extract and clean user and message
	string userAndMsg = client[i].rest;
	userAndMsg = ltrim(userAndMsg);
	string reciever = " ";
	string message = " ";
	
	//looking for the first whitespace that seperates user from message
	size_t seperator = userAndMsg.find(' ');
    if(seperator != string::npos) {
		//this is the extracted reciever
        reciever = userAndMsg.substr(0, seperator);
		//this is the extracted message
        message = userAndMsg.substr(seperator + 1); 
    } 
	bool foundUser = false;
	//add null term to message
	message = client[i].username + ": " + message + "\n";
	//now we loop through looking for the username
	for(int j = 0; j < MAXCONN; j++) {
		//found user
		if(client[j].username == reciever){
			//sends over the message only to them
			const char* msg = message.c_str();
			write(client[j].socket, msg, strlen(msg));
			foundUser = true;
			printUserNameLine(client, j, client[j].username, client[j].socket);
		}
	}
	//if user not online, we are told
	if (foundUser == false){
		string error = reciever + " is not online!\n";
		const char* error_msg = error.c_str();
		write(client[i].socket, error_msg, strlen(error_msg));
	}
}

void sig_chld(int signo){
	pid_t pid;
	int stat;
	while ((pid = waitpid(-1, &stat, WNOHANG)) > 0) 
		printf("child %d terminated.\n", pid);
	return ;
}

int main(int argc, char * argv[])
{
	int sockfd, rec_sock, len, i;
	struct sockaddr_in addr, recaddr;
	struct sigaction abc;
	// MAXCONN is = 20
	clientInfo client[20];

	char buf[100];
	fd_set allset, rset;
	int maxfd;

	abc.sa_handler = sig_chld;
	sigemptyset(&abc.sa_mask);
	abc.sa_flags = 0;

	sigaction(SIGCHLD, &abc, NULL);

	if (argc < 2) {
		printf("Usage: a.out port.\n");
		exit(0);
	}

	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror(": Can't get socket");
		exit(1);
	}

	addr.sin_addr.s_addr = INADDR_ANY;
	addr.sin_family = AF_INET;
	addr.sin_port = htons((short)atoi(argv[1]));

	if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
		perror(": bind");
		exit(1);
	}

	len = sizeof(addr);
	if (getsockname(sockfd, (struct sockaddr *)&addr, (socklen_t *)&len) < 0) {
		perror(": can't get name");
		_exit(1);
	}

	printf("ip = %s, port = %d\n", inet_ntoa(addr.sin_addr), htons(addr.sin_port));

	if (listen(sockfd, 5) < 0) {
		perror(": bind");
		exit(1);
	}

	// init client array and file descriptor set
	for (i=0; i<MAXCONN; i++){
		client[i].socket = -1;
	}

	FD_ZERO(&allset);
	FD_SET(sockfd, &allset);
	maxfd = sockfd;

	while (1) {
		rset = allset;
		select(maxfd+1, &rset, NULL, NULL, NULL);
		if (FD_ISSET(sockfd, &rset)) {
			/* somebody tries to connect */
			if ((rec_sock = accept(sockfd, (struct sockaddr*)(&recaddr), (socklen_t *)&len)) < 0) {
				if (errno == EINTR)
					continue;
				else {
					perror(":accept error");
					exit(1);
				}
			}
			/* print the remote socket information */
			printf("remote machine = %s, port = %d.\n",
					inet_ntoa(recaddr.sin_addr), ntohs(recaddr.sin_port)); 

			// here is where we add the client to the array/update socket 
			for (i=0; i<MAXCONN; i++) {
				if (client[i].socket < 0) {
					client[i].socket = rec_sock; 
					FD_SET(client[i].socket, &allset);
					
					// send welcome message
					//printNotice(client[i].socket);
					const char *welcomeMsg = "\nWelcome! Enter a username: ";
					write(rec_sock, welcomeMsg, strlen(welcomeMsg));
					client[i].welcomeChoice = true; 
					break;
				}
			}
			if (i== MAXCONN) {
				printf("too many connections.\n");
				close(rec_sock);
			}
			if (rec_sock > maxfd) maxfd = rec_sock;
		}
		for (i=0; i<MAXCONN; i++) {
			if (client[i].socket < 0) continue;
			if (FD_ISSET(client[i].socket, &rset)) {
				int num;
				num = read(client[i].socket, buf, 100);
				if (num == 0) {
					/* client exits */
					close(client[i].socket);
					FD_CLR(client[i].socket, &allset);
					client[i].socket = -1;
					NUM_USERS--;
				} 
				else {
					// clean up input
					//null term input
					buf[num] = '\0';
					rtrim(buf);
                    // make the buffer a string
                    string input_message(buf);
                    istringstream iss(input_message);
                    // get just the command
                    string command;
                    iss >> command;
                    // get the rest of the line
                    string rest;
                    getline(iss, rest);
					client[i].command = command;
					client[i].rest = rest;

					if(client[i].welcomeChoice == true){
						// get info from welcome message
						welcomeChoiceFunc(client, i);
					}
					else{	
						// menu choices 
						if(client[i].waitingForCommand == true){
							if(client[i].command == "who"){
								who(client, i);
							}
							else if(client[i].command == "?" || client[i].command == "help"){
								printHelp(client, i);
							}
							else if(client[i].command == "quit" || client[i].command == "exit"){
								//normal exit code
								close(client[i].socket);
								FD_CLR(client[i].socket, &allset);
								client[i] = clientInfo{};
								client[i].socket = -1;
								NUM_USERS--;
							}
							
							else if(client[i].command == "shout"){
								shout(client, i);
							}
							else if(client[i].command == "tell"){
								if(client[i].rest.empty()){
									const char *msg = "\nMissing username or message: tell <user> <msg> \n";
									write(client[i].socket, msg, strlen(msg));
								}
								else
									tell(client, i);
							
							}
							else{
								const char *msg = "Command not supported.\n";
							    write(client[i].socket, msg, strlen(msg));
							}
						}// end of waiting for command 
					printUserNameLine(client, i, client[i].username, client[i].socket);
					} // end of command else 
				}// end of big else
			}
		}
	}
}
