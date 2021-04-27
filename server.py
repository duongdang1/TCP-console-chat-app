import socket
import select
import struct
import sys
import pickle

HEADER_LENGTH = 1024


IP = "127.0.0.1"
PORT = 9669

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))

server_socket.listen()

conversation ={
    1 : '1.txt',

    2 : '2.txt'
}
users = [
    {
        'username': 'user1',
        'user_id': 1
    },
    {
        'username': 'user2',
        'user_id': 2
    },
    {
        'username': 'user3',
        'user_id': 3
    },
    {
        'username': 'user4',
        'user_id': 4
    },
    {
        'username': 'user5',
        'user_id': 5
    }
]

def login(username):
    
    for user in users:
        if user['username'] == username:
            # print ("ok")
            return user['username'], user["user_id"]
        
    return None
        
# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
sessions = {}

#function to find the client's socket that the the current notified socket want to send the message to.
def getRecvSocket(user_id):
    try:
        return sessions[user_id]
    except:
        return None, None

#Send error message to the client if error's found
def sendErrorMes(socketid, mes):
    package = [9]
    length = len(mes)
    if length > 1019:
        length = 1019
    package += struct.pack("I", length)
    package += mes

print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def receive_message(client_socket):
    try:
        receive_message = client_socket.recv(HEADER_LENGTH)
        return receive_message
    except:
        return False

while True:

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            client_socket, client_address = server_socket.accept()
            
            sockets_list.append(client_socket)
            
        else:
        # Receive message
        # Receive package from clients in three types
            package = receive_message(notified_socket)
            package_type = package[0]
            
            # type 1 is login request
            # the package includes: package type, username
            if package_type == 1:
                size = struct.unpack("I", package[1:5])
                if size[0] > 1019:
                    continue
                username = package[5:5+size[0]]
                username = username.decode()
                user,tag = login(username)
                
                if login(username) == None: 
                    notified_socket.send(b"no user found")
                    
                else: 
                    sessions[notified_socket] = tag
                    
                    notified_socket.send((b"Welcome to the server"))

            #type 2 is conversation transcript request
            #the package includes: package type, conversation's id
            elif package_type == 2: 
                
                convo_id = package[1]
                
                f =  open(conversation[convo_id], 'rb')
 
                l = f.read(1024)
                notified_socket.send(l)
                print('send successful')
                continue
                
            #type 3 is send message request
            #the package includes: package type, receiver's id, message
            elif package_type == 3:
                recv_id = package[1]
                conv_id = package[2]
                size = struct.unpack("I", package[3:7])
                if size[0] > 1015:
                    continue
            
                if getRecvSocket(recv_id) == None:
                    sendErrorMes(notified_socket, "User is offline")
                else:
                    message = package[7:7+size[0]]
                    message = message.decode()
                   
                    for client_socket in sessions:
                        #send message to the designated user and not to the user that sent the message
                        if client_socket != notified_socket and sessions[client_socket] == recv_id:
                            #also write to the conversation transcript
                            with open(conversation[conv_id], "a") as f:
                                f.write("\n" + str(sessions[notified_socket])+ ">" + message)
                                f.close()
                            client_socket.send((str(sessions[notified_socket])+ "`" + message).encode())
                            

                    if message is False:
                        # print('Closed connection from: {}'.format(user))

                        # Remove from list for socket.socket()
                        sockets_list.remove(notified_socket)

                        # Remove from our list of users
                        del sessions[notified_socket]

                        continue
            
            