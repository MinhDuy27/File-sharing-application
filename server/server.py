import socket
import threading
import json
import select
import time
# Server configuration
HOST = '192.168.5.100'  
PORT = 10000
# Store client information and files
clients = {}
threads = []
termination_flag = False
host = socket.getaddrinfo(HOST,PORT)

# Handle client requests
def handle_client(conn):
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        command = data.split(' ')
        clients_tuples = (command[1],command[2])
        global clients
        if command[0] == 'connect':
            if clients_tuples not in clients:
                clients[clients_tuples] = []
            conn.sendall('done'.encode())
        if command[0] == 'publish':
            file_name = command[3] 
            clients[clients_tuples].append(file_name)
            conn.sendall('server received publish message'.encode())             
        elif command[0] == 'fetch':
            found_clients = []
            file_name = command[3] 
            for key, value_list in clients.items():
                if file_name in value_list:
                    found_clients.append(key)
            serialized_list = json.dumps(found_clients)
            conn.sendall(serialized_list.encode())
        elif command[0] == 'viewfname':
            new_dict = {str(key): value for key, value in clients.items() if key != clients_tuples}
            clients_json = json.dumps(new_dict)
            conn.sendall(clients_json.encode())     
        elif command[0] == 'disconnect':
            clients.pop(clients_tuples,None)
            conn.sendall('disconnected'.encode())
    conn.close()

def discoverHost(hostip,hostport):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((hostip, int(hostport)))
        command = 'discover'
        client.sendall(command.encode())
        response = client.recv(1024).decode()
        print(response)

def pinghost(hostip,hostport):
    client =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((hostip, int(hostport)))
        print(f"{hostip}:{hostport} is live")
    except ConnectionRefusedError:
        print(f"{hostip}:{hostport} is not live.")   
    finally:
        client.close()

def handle_input(InputRequest,hostip,hostport): 
        if InputRequest == 'discover':
           discoverHost(hostip,hostport)
        elif InputRequest == 'ping':
           pinghost(hostip,hostport)
           

#Start the server
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(30)
        global termination_flag
        while not termination_flag:
            try:
                ready_sockets, _, _ = select.select([server], [], [], 0.1)
                if server in ready_sockets:
                    conn, addr = server.accept()
                    client_thread = threading.Thread(target=handle_client, args=(conn,))
                    threads.append(client_thread)
                    client_thread.start()
            except socket.timeout:
                continue

def exitprogram():
    global threads
    for thread in threads:
        thread.join()

def interact ():
    global termination_flag
    while not termination_flag:
        command = input('Enter command: ')
        parts = command.split(' ')
        if parts[0] == 'exitprogram':
            exitprogram()
            termination_flag = True
        elif parts[0] == 'viewclients':
            global clients
            if len(clients) == 0:
                print("empty client list")
            else: 
                for key, values in clients.items():
                    print(key, values)    
        else:
            handle_input(parts[0],parts[1],parts[2])
if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    interaction_thread = threading.Thread(target=interact)
    interaction_thread.start()
    server_thread.start()

   