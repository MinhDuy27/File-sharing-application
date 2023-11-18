import socket
import threading
import os
import json
import sys
import time
import select
# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000

# Client configuration
CLIENT_HOST = '127.0.0.1'
CLIENT_PORT = 9001
termination_Flag = False
# Store local files
clients_localfile=[]
threads = []
# Send command to the server
def send_command_server(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((SERVER_HOST, SERVER_PORT))
        client.sendall(command.encode())
        response = client.recv(1024).decode()
        return response
#send command to the host    
def send_command_host(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        parts = command.split(' ')
        client.connect((parts[1],int(parts[2])))
        client.sendall(command.encode())
        response = client.recv(1024).decode()
        return response
    
# Handle incoming file requests from other clients or server
def handle_requests():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:  # ipv4 - AF_Inet , tcp - SOCK_STREAM
        server.bind((CLIENT_HOST, CLIENT_PORT))
        server.listen()
        server.settimeout(1)
        global termination_Flag
        while not termination_Flag:
            try:
                ready_sockets, _, _ = select.select([server], [], [], 0.1)
                if server in ready_sockets:
                    conn, addr = server.accept()
                    # Handle the connection
                    request_thread = threading.Thread(target=handle_request, args=(conn,))
                    threads.append(request_thread)
                    request_thread.start()
            except socket.timeout:
                continue
            
# Handle each file request
def handle_request(conn):
    data = conn.recv(1024).decode()
    command = data.split(' ')
    if command[0] == 'fetch':
        file_name = command[3]
        folder_name = "local_file"
        directory_path = "D:/MMT-BTL1.2/client1"
        file_path = os.path.join(directory_path, folder_name, file_name)
        with open(file_path, "r") as file: #read the file contents
            file_contents = file.read()
            file_contentsjson = json.dumps(file_contents)
            conn.sendall(file_contentsjson.encode())
    elif command[0] == 'discover':
        refresh()
        global clients_localfile
        localfile_json = json.dumps(clients_localfile)
        conn.sendall(localfile_json.encode())
    conn.close()

def refresh():
    global clients_localfile 
    clients_localfile = []
    folder_path ="D:/MMT-BTL1.2/client1/local_file"
    for file in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file)):
            clients_localfile.append(file)
    
    

# Publish a local file to the server
def publish_local_file( file_name):
    send_command_server(f'publish {CLIENT_HOST} {CLIENT_PORT} {file_name}') # f allow to embed CLient_HOST to { }
    data = "published"
    return data

# Fetch a file from the server
def fetch_file(file_name):
    clientList  = send_command_server(f'fetch {CLIENT_HOST} {CLIENT_PORT} {file_name}') # send command to client to get a list of port that have filename
    print (clientList)
    command = input('chose client to fetch file : ')
    parts = command.split(' ')
    result = send_command_host(f'fetch {parts[0]} {parts[1]} {file_name}')
    directory_path = "D:/MMT-BTL1.2/client1"
    folder_name = "local_file"
    file_path = os.path.join(directory_path, folder_name, file_name)
    with open(file_path, 'w') as file: # wtite the file contents
        file.write(result)
    publish_local_file(file_name) # notify to server
    print('fetched file')

def viewfNameinServer():
    fnamelist  = send_command_server(f'viewfname {CLIENT_HOST} {CLIENT_PORT}')
    data_dict = eval(fnamelist)
    for key, values in data_dict.items():
        print(key, values)


def writelocalfile(local_name,contnet) :
    store_file_name = local_name 
    directory_path = "D:/MMT-BTL1.2/client1"
    folder_name = "local_file"
    file_path = os.path.join(directory_path, folder_name, store_file_name)
    with open(file_path, 'w') as file:
        file.write(contnet)
    clients_localfile.append(local_name)
    print('done')

def exitprogram():
    global threads
    for thread in threads:
        thread.join()
def connecttoserver():
    result = send_command_server(f'connect {CLIENT_HOST} {CLIENT_PORT}')
    print(result)

def disconnecttoserver():
    data = send_command_server(f'disconnect {CLIENT_HOST} {CLIENT_PORT}')
    return data

def interact():
    global termination_Flag
    while not termination_Flag:
        command = input('Enter command: ')
        parts = command.split(' ')
        if parts[0] == 'connect':
            connecttoserver()
        elif parts[0] == 'publish':
            file_name = parts[1]
            print(publish_local_file( file_name))
        elif parts[0] == 'fetch':
            file_name = parts[1]
            fetch_file(file_name)
        elif parts[0] == 'viewfname':
            viewfNameinServer()
        elif parts[0] == 'disconnect':
            disconnecttoserver()
        elif parts[0] == 'writelocalfile':
            local_name = parts[1]
            content = ' '.join(parts[2:])
            writelocalfile(local_name,content)
        elif parts[0] == 'refresh':
            refresh()
            global clients_localfile
            print(clients_localfile)
        elif parts[0] == 'exitprogram':
            exitprogram()
            disconnecttoserver()
            termination_Flag = True

        
if __name__ == '__main__':
    server_thread = threading.Thread(target=handle_requests)
    interaction_thread = threading.Thread(target=interact)
    server_thread.start()
    interaction_thread.start()
    