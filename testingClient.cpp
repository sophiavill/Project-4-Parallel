#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <server_ip> <server_port>\n";
        return 1;
    }

    const char *server_ip = argv[1];
    int server_port = std::stoi(argv[2]);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        std::cerr << "Error: Could not create socket\n";
        return 1;
    }

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(server_port);
    inet_pton(AF_INET, server_ip, &server_addr.sin_addr);

    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Error: Connection failed\n";
        close(sockfd);
        return 1;
    }
    
    char buffer[1024];

    // Receive and print response from server
    int bytes_received = recv(sockfd, buffer, sizeof(buffer), 0);
    if (bytes_received < 0) {
        std::cerr << "Error in receiving data\n";
    } else if (bytes_received == 0) {
        std::cout << "Server disconnected\n";
    } else {
        buffer[bytes_received] = '\0';
        std::cout << buffer << std::endl;
    }

    while (true) {
        std::string message;
        std::getline(std::cin, message);

        // Check if the message is empty
        if (message.empty()) {
            // If empty, send a newline character
            send(sockfd, "\n", 1, 0);
        } else {
            // Otherwise, send the message
            send(sockfd, message.c_str(), message.length(), 0);
        }

        // Receive and print response from server
        bytes_received = recv(sockfd, buffer, sizeof(buffer), 0);
        if (bytes_received < 0) {
            std::cerr << "Error in receiving data\n";
            break;
        } else if (bytes_received == 0) {
            std::cout << "Server disconnected\n";
            break;
        } else {
            buffer[bytes_received] = '\0';
            std::cout << buffer << std::endl;
        }
    }

    close(sockfd);
    std::cout << "Connection closed\n";

    return 0;
}
