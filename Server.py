import socket 
import threading
import pickle
from ChatRoom import ChatRoom
HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
BROADCASTADDR=(SERVER,5972)
ChatRooms=[] # will be a array of tuples (Room Name, Related Server address)


AllconnectedComp={} # THIS IS A DICTIONARY THAT STORES THE ADDRESS AND THE SOCKET CONNECTION FOR EACH CONNECTED CLIENT 
                    # (IF THE CLIENTS HAVE SAME IP ADDRESS LIKE MULTIPLE CLIENTS ON SAME PC THEN THERE CONN WILL BE OVERRIDDEB)

# broadcast socket to listen for broadcasted message from clients
brodcast_server_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
brodcast_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
brodcast_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
brodcast_server_socket.bind(BROADCASTADDR)




# server socket that client use to send after succesfull client registeration
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# THIS FUNCTION HANDLE ANY CLIENT SENDING TO THE SERVER (NOT BRODCASTED MESSAGES)
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    # YOU WILL BE LOOPING UNTILL THE CLIENT SENDS THE DISCONNECT MESSAGE TO CLOSE THE CONNECTION
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            # Send Messages from clients to other clients on same chatroom
            if msg[:2]=="/M":
                Message = msg.split(" ")
                if len(Message)>1:
                    roomname = Message[1]
                    for x in ChatRooms:
                        if x.name == roomname and (addr[1]  in x.users):
                            for socketnum in x.users:
                                if not(addr[1]== socketnum):
                                    if len(Message)>2:
                                         AllconnectedComp[socketnum][1].send(Message[2].encode(FORMAT))

            # CREATE A CHAT ROOM AND ADD THE USER HOW CREATED IT

            if msg[:7]=="/CREATE":
                # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                if len(msg)>8:
                    CreateRoom(addr[1],msg[8:],SERVER)
                    conn.send(f"Room with name {msg[8:]} is created".encode(FORMAT))
                    for key, value in AllconnectedComp.items():
                        print(key, value)
                        if not(key == addr[1]):
                            value[1].send(f"A new Room named {msg[8:]} was Created by User {addr[0]}".encode(FORMAT))

                else:
                    conn.send("Please Specify the name of the chatroom you want to create".encode(FORMAT))       
            # CLIENT SEND A MESSAGE TO JOIN AN EXISTANT CHAT ROOMS
            if msg[:5]=="/JOIN":
                # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                if len(msg)>6:
                    room = RoomSearch(msg[6:])
                    if not(room ==None):
                        room.add_user(addr[1])
                        conn.send(F"You have joined {room.name} chatroom".encode(FORMAT))       
                    else:
                        conn.send(F"There is no chatroom with name: {room.name}".encode(FORMAT))       
            
                else:
                    conn.send("Please Specify the name of the chatroom you want to join".encode(FORMAT))       
            #  CHECK FOR THE DISCONNECT MESSAGE
            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr}] {msg}")

            # if len(ChatRooms)==0:
            #     conn.send("There is no Chat Rooms available If you want Create one Please Confrim with /CONFIRM !!".encode(FORMAT))
            # else:
            #     conn.send([x for x in ChatRooms])    

    conn.close()
        

def CreateRoom(user,name,server_iP):
    newChatRoom=ChatRoom(name,server_iP)    
    newChatRoom.add_user(user)
    newChatRoom.set_leader(user)
    ChatRooms.append(newChatRoom)
def RoomSearch(chatroom_name):
    for x in ChatRooms:
        if x.name==chatroom_name:
            return x
    return None

# This is a function on it's own thread where it just listens for any client connection 
def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    # we accept any connection , then we create a new thread for this connection so we can communicate with it by handle connection function
    while True:
        conn, addr = server.accept()
        AllconnectedComp[addr[1]]=[addr[0],conn]
        conn.send(str(addr[1]).encode(FORMAT))
        thread = threading.Thread(target=handle_client, args=(conn, addr))      
        thread.start()
        
        # print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

# This is a broadcast function which listens for all broadcasted message from any client and sends all available chatrooms to the client
def broadStart():
    print(f"[LISTENING] Server is listening brodcasts on {BROADCASTADDR}")
    while True:
        message, addr = brodcast_server_socket.recvfrom(64)
  
        message= message.decode(FORMAT)
        message,Type= message.split(",")[0],message.split(",")[1]
        print(message)
        if len(message.split(":"))==2:

            if message.split(":")[0]=="CONN":
                # try:
                connect_to_client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connect_to_client_socket.connect((addr[0],int(message.split(":")[1])))

                # except:
                #     print("yoU WERE TRYING TO CONNECT TO AN ALREADY CONNECTION ")
            
                continue

        


        print(message, Type)
        # SendRoomsThread = threading.Thread(target=SendRooms, args=(senderIP,addr,Type))
        # SendRoomsThread.start()
        SendRooms(int(message),addr,Type)
def SendRooms(ConnNumber,addr,Type):
    print(addr)
    if  ConnNumber and Type:
        print(f"Sending Chat Rooms available to Client who Requested it with {addr[0]}")
        if len(ChatRooms)==0:
            AllconnectedComp[ConnNumber][1].send(str("Sorry there is no Chat ROOMS , Please create one by /CREATE").encode(FORMAT))
        else:
            AllconnectedComp[ConnNumber][1].send(str("Here are the available Rooms \n").encode(FORMAT))
            for x in ChatRooms:
                message=x.name+","+ x.server_on+"\n"
                AllconnectedComp[ConnNumber][1].send(message.encode(FORMAT))
            AllconnectedComp[ConnNumber][1].send(str("If you want to create a Chat Room for you you can also create one by /CREATE").encode(FORMAT))


def begin():
    thread= threading.Thread(target=start)
    broadthread= threading.Thread(target=broadStart)
    broadthread.start()
    thread.start()


print("[STARTING] server is starting...")
begin()