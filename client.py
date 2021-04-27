import socket
import select
import errno
import sys, struct
import pickle
from threading import Thread

HEADER_LENGTH = 1024
IP = "127.0.0.1"
PORT = 9669

#Function to build packages that will be sent to the server
def send_login_request(username):
    type_pac = 1
    package_type = type_pac.to_bytes(1,'big')
    length = len(username)
    if length > 1019:
        print ("Error: Username too long")
        sys.exit()
    package = package_type + struct.pack("I", length) + username.encode()
    # package = pad(package)
    
    return package

def send_message(recv_id, conv_id, message):
    type_pac = 3
    package_type = type_pac.to_bytes(1,"big")
    recv_id = recv_id.to_bytes(1,'big')
    conv_id = conv_id.to_bytes(1,'big')
    length = len(message)
    if length > 1015:
        print('message too long')
        sys.exit()
    package = package_type + recv_id + conv_id + struct.pack('I', length) + message.encode()
   
    return package

def send_con_request(conv_id):
    type_pac = 2
    package_type = type_pac.to_bytes(1,"big")
    conv_id = conv_id.to_bytes(1,'big')
    length = len(conv_id)
    if length > 1015:
        print('id too long')
        sys.exit()
    package = package_type + conv_id
   
    return package

def send(message,recv_id,con_id):
    if message: 
        message = send_message(recv_id,con_id,message)
        client_socket.send(message)

def recv():
    try:
        message_receiver = client_socket.recv(HEADER_LENGTH).decode()
        message = message_receiver.split('`')
        # Print message
        print(f'\r{message[0]}> {message[1]}')

    except IOError as e :
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
    except Exception as e:
            # Any other exception - something happened, exit
            print('Reading error: {}'.format(str(e)))
            sys.exit()

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to a given ip and port
client_socket.connect((IP, PORT))

#login request
my_username = input("Username: ")
request = send_login_request(my_username)   
client_socket.send(request)

#Wait for server response
username_conf = client_socket.recv(1024).decode()

if username_conf == "Welcome to the server":
    con_id = int(input("Please enter conversation's id: "))
    con_request = send_con_request(con_id)
    client_socket.send(con_request)
    conversation_file = client_socket.recv(HEADER_LENGTH).decode()
    print(conversation_file)

    recv_id = int(input("please enter receiver's id: "))
    while True:
            # Wait for user to input a message

            message = input(f'{my_username} > ')
            # 2 threads to handle conversations
            # 1 thread for handling sending messages
            # 1 thread for handling receving messages
            send_thread = Thread(target=send, args= (message, recv_id, con_id))
            send_thread.start()
            recv_thread = Thread(target=recv)
            recv_thread.start()

         