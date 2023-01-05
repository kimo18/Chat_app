import socket 
import threading
import pickle
import sys
from ChatRoom import ChatRoom


class Server:
    HEADER = 64
    PORT = 5050   # todel
    SERVER = socket.gethostbyname(socket.gethostname()) #todel
    ADDR = (SERVER, PORT) #todel
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    is_leader = False
    server_ip =socket.gethostbyname(socket.gethostname())
    port = 0
    ADDR=(server_ip,0)
    BROADCASTADDR=(server_ip,5972)
    SERVERSERVERADDR=(server_ip,6060)
    max_connections = 0
    server_dic={}
    current_connections = 0
    number_servers=1
    chat_rooms=[]
    all_connected_client={}

# Intializing broadcast server to listen from other componenets
    broadcast_server_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_server_socket.bind(BROADCASTADDR)

    server_server_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # server_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Intializing TCP Server to listen from Clients messages
    server_tolisten_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leaderserver_to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, is_leader,port=5050, max_connections=5):
        self.is_leader = is_leader=="True"
        self.port = int(port)
        # self.broadStart()
        self.ADDR=(self.server_ip,self.port)
        self.server_tolisten_socket.bind(self.ADDR)
        self.max_connections = max_connections
        if self.is_leader:
            self.server_server_socket.bind(self.SERVERSERVERADDR)
            threading.Thread(target=self.ServerBroadListen).start()
            

        else:
            self.leaderserver_to_server_socket.bind((self.server_ip, 0))
            self.s_broadcast(6060,f"CONN:{self.leaderserver_to_server_socket.getsockname()[1]}")
            threading.Thread(target=self.serverlisten).start()

# _________________________________________________________________________________________

    def handle_client(self,conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")

        connected = True
        # YOU WILL BE LOOPING UNTILL THE CLIENT SENDS THE DISCONNECT MESSAGE TO CLOSE THE CONNECTION
        while connected:
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.FORMAT)

                # Send Messages from clients to other clients on same chatroom
                if msg[:2]=="/M":
                    Message = msg.split(" ")
                    if len(Message)>1:
                        roomname = Message[1]
                        for x in self.chat_rooms:
                            if x.name == roomname and (addr[1]  in x.users):
                                for socketnum in x.users:
                                    if not(addr[1]== socketnum):
                                        if len(Message)>2:
                                            self.all_connected_client[socketnum][1].send(Message[2].encode(self.FORMAT))

                # CREATE A CHAT ROOM AND ADD THE USER HOW CREATED IT

                if msg[:7]=="/CREATE":
                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg)>8:
                        self.CreateRoom(addr[1],msg[8:],self.server_ip)
                        conn.send(f"Room with name {msg[8:]} is created".encode(self.FORMAT))
                        for key, value in self.all_connected_client.items():
                            print(key, value)
                            if not(key == addr[1]):
                                value[1].send(f"A new Room named {msg[8:]} was Created by User {addr[0]}".encode(self.FORMAT))

                    else:
                        conn.send("Please Specify the name of the chatroom you want to create".encode(self.FORMAT))       
                # CLIENT SEND A MESSAGE TO JOIN AN EXISTANT CHAT ROOMS
                if msg[:5]=="/JOIN":
                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg)>6:
                        room = self.RoomSearch(msg[6:])
                        if not(room ==None):
                            room.add_user(addr[1])
                            conn.send(F"You have joined {room.name} chatroom".encode(self.FORMAT))       
                        else:
                            conn.send(F"There is no chatroom with name: {room.name}".encode(self.FORMAT))       
                
                    else:
                        conn.send("Please Specify the name of the chatroom you want to join".encode(self.FORMAT))       
                #  CHECK FOR THE DISCONNECT MESSAGE
                if msg == self.DISCONNECT_MESSAGE:
                    connected = False

                print(f"[{addr}] {msg}")

                # if len(ChatRooms)==0:
                #     conn.send("There is no Chat Rooms available If you want Create one Please Confrim with /CONFIRM !!".encode(FORMAT))
                # else:
                #     conn.send([x for x in ChatRooms])    

        conn.close()
 # _________________________________________________________________________________________
       
    def CreateRoom(self,user,name,server_iP):
        newChatRoom=ChatRoom(name,server_iP)    
        newChatRoom.add_user(user)
        newChatRoom.set_leader(user)
        self.chat_rooms.append(newChatRoom)
# _________________________________________________________________________________________

    def RoomSearch(self,chatroom_name):
        for x in self.chat_rooms:
            if x.name==chatroom_name:
                return x
        return None
# _________________________________________________________________________________________
    def start(self):
        self.server_tolisten_socket.listen()
        print(f"[LISTENING] Server is listening on {self.server_ip, self.port}")
        # we accept any connection , then we create a new thread for this connection so we can communicate with it by handle connection function
        while True:
            conn, addr = self.server_tolisten_socket.accept()
            self.all_connected_client[addr[1]]=[addr[0],conn]
            conn.send(str(addr[1]).encode(self.FORMAT))
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))      
            thread.start()
# _________________________________________________________________________________________
    def serverlisten(self):
        self.leaderserver_to_server_socket.listen()
        while True:
            conn, addr = self.leaderserver_to_server_socket.accept()
            print(addr)
            thread = threading.Thread(target=self.server_recv, args=(conn, addr))      
            thread.start()
# _________________________________________________________________________________________
    def server_recv(self, conn, addr):
        while True:
            message = conn.recv(4096)
            message=pickle.loads(message)
            self.server_dic=message[0]
            self.number_servers=message[1]
            self.chat_rooms=message[2]
            if message:
                print(self.chat_rooms,self.number_servers,self.server_dic)

# _________________________________________________________________________________________
    def broadStart(self):
        print(f"[LISTENING] Server is listening brodcasts on {self.BROADCASTADDR}")
        while True:
            message, addr = self.broadcast_server_socket.recvfrom(64)
    
            message= message.decode(self.FORMAT)
            message,Type= message.split(",")[0],message.split(",")[1]
            print(message)
            if len(message.split(":"))==2:

                if message.split(":")[0]=="CONN":
                    # try:
                    if self.is_leader:
                        print(f"Leader with address: {self.server_ip}")
                        connect_to_client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        connect_to_client_socket.connect((addr[0],int(message.split(":")[1])))

                    # except:
                    #     print("yoU WERE TRYING TO CONNECT TO AN ALREADY CONNECTION ")
                
                    continue

            


            print(message, Type)
            # SendRoomsThread = threading.Thread(target=SendRooms, args=(senderIP,addr,Type))
            # SendRoomsThread.start()
            self.SendRooms(int(message),addr,Type)
# _________________________________________________________________________________________

    def SendRooms(self,ConnNumber,addr,Type):
        print(addr)
        if  ConnNumber and Type:
            print(f"Sending Chat Rooms available to Client who Requested it with {addr[0]}")
            if len(self.chat_rooms)==0:
                self.all_connected_client[ConnNumber][1].send(str("Sorry there is no Chat ROOMS , Please create one by /CREATE").encode(self.FORMAT))
            else:
                self.all_connected_client[ConnNumber][1].send(str("Here are the available Rooms \n").encode(self.FORMAT))
                for x in self.chat_rooms:
                    message=x.name+","+ x.server_on+"\n"
                    self.all_connected_client[ConnNumber][1].send(message.encode(self.FORMAT))
                self.all_connected_client[ConnNumber][1].send(str("If you want to create a Chat Room for you you can also create one by /CREATE").encode(self.FORMAT))

# _________________________________________________________________________________________

    def s_broadcast(self,port,message):

        MESSAGE = message+","+"Server"
        self.server_server_socket.sendto(MESSAGE.encode(self.FORMAT), ("255.255.255.255", port))
# _________________________________________________________________________________________

    def ServerBroadListen(self):
        print(f"[LISTENING] Server is listening brodcasts from Servers on {self.SERVERSERVERADDR}")
        while True:
            message, addr = self.server_server_socket.recvfrom(self.HEADER)
            message= message.decode(self.FORMAT)
            message,Type= message.split(",")[0],message.split(",")[1]
            print(message,"kofta")
            if len(message.split(":"))==2:

                if message.split(":")[0]=="CONN":
                    connect_to_server_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    connect_to_server_socket.connect((addr[0],int(message.split(":")[1])))
                    self.server_dic[connect_to_server_socket.getsockname()[1]]=[connect_to_server_socket.getpeername()[0],connect_to_server_socket.getpeername()[1],connect_to_server_socket.getsockname()[0]]
                    self.number_servers= self.number_servers+1     
                    to_send = pickle.dumps([self.server_dic,self.number_servers,self.chat_rooms]) #self.all_connected_client
                    connect_to_server_socket.send(to_send)
                    continue

# _________________________________________________________________________________________

    def begin(self):
        thread= threading.Thread(target=self.start)
        broadthread= threading.Thread(target=self.broadStart)
        broadthread.start()
        thread.start()
# _________________________________________________________________________________________

def main(is_leader,port):
    our_server= Server(is_leader,port)
    print(our_server.port,our_server.is_leader)
    print("[STARTING] server is starting...")
    our_server.begin()
    

if __name__ == "__main__":

    print(sys.argv)
    main(sys.argv[1],sys.argv[2])



# ChatRooms=[] # will be a array of tuples (Room Name, Related Server address)
# AllconnectedComp={} # THIS IS A DICTIONARY THAT STORES THE ADDRESS AND THE SOCKET CONNECTION FOR EACH CONNECTED CLIENT 

# broadcast socket to listen for broadcasted message from clients





# server socket that client use to send after succesfull client registeration
# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.bind(ADDR)

# THIS FUNCTION HANDLE ANY CLIENT SENDING TO THE SERVER (NOT BRODCASTED MESSAGES)
# def handle_client(conn, addr):
#     print(f"[NEW CONNECTION] {addr} connected.")

#     connected = True
#     # YOU WILL BE LOOPING UNTILL THE CLIENT SENDS THE DISCONNECT MESSAGE TO CLOSE THE CONNECTION
#     while connected:
#         msg_length = conn.recv(HEADER).decode(FORMAT)
#         if msg_length:
#             msg_length = int(msg_length)
#             msg = conn.recv(msg_length).decode(FORMAT)

#             # Send Messages from clients to other clients on same chatroom
#             if msg[:2]=="/M":
#                 Message = msg.split(" ")
#                 if len(Message)>1:
#                     roomname = Message[1]
#                     for x in ChatRooms:
#                         if x.name == roomname and (addr[1]  in x.users):
#                             for socketnum in x.users:
#                                 if not(addr[1]== socketnum):
#                                     if len(Message)>2:
#                                          AllconnectedComp[socketnum][1].send(Message[2].encode(FORMAT))

#             # CREATE A CHAT ROOM AND ADD THE USER HOW CREATED IT

#             if msg[:7]=="/CREATE":
#                 # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
#                 if len(msg)>8:
#                     CreateRoom(addr[1],msg[8:],SERVER)
#                     conn.send(f"Room with name {msg[8:]} is created".encode(FORMAT))
#                     for key, value in AllconnectedComp.items():
#                         print(key, value)
#                         if not(key == addr[1]):
#                             value[1].send(f"A new Room named {msg[8:]} was Created by User {addr[0]}".encode(FORMAT))

#                 else:
#                     conn.send("Please Specify the name of the chatroom you want to create".encode(FORMAT))       
#             # CLIENT SEND A MESSAGE TO JOIN AN EXISTANT CHAT ROOMS
#             if msg[:5]=="/JOIN":
#                 # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
#                 if len(msg)>6:
#                     room = RoomSearch(msg[6:])
#                     if not(room ==None):
#                         room.add_user(addr[1])
#                         conn.send(F"You have joined {room.name} chatroom".encode(FORMAT))       
#                     else:
#                         conn.send(F"There is no chatroom with name: {room.name}".encode(FORMAT))       
            
#                 else:
#                     conn.send("Please Specify the name of the chatroom you want to join".encode(FORMAT))       
#             #  CHECK FOR THE DISCONNECT MESSAGE
#             if msg == DISCONNECT_MESSAGE:
#                 connected = False

#             print(f"[{addr}] {msg}")

#             # if len(ChatRooms)==0:
#             #     conn.send("There is no Chat Rooms available If you want Create one Please Confrim with /CONFIRM !!".encode(FORMAT))
#             # else:
#             #     conn.send([x for x in ChatRooms])    

#     conn.close()
        

# def CreateRoom(user,name,server_iP):
#     newChatRoom=ChatRoom(name,server_iP)    
#     newChatRoom.add_user(user)
#     newChatRoom.set_leader(user)
#     ChatRooms.append(newChatRoom)
# def RoomSearch(chatroom_name):
#     for x in ChatRooms:
#         if x.name==chatroom_name:
#             return x
#     return None

# This is a function on it's own thread where it just listens for any client connection 
# def start():
#     server.listen()
#     print(f"[LISTENING] Server is listening on {SERVER}")
#     # we accept any connection , then we create a new thread for this connection so we can communicate with it by handle connection function
#     while True:
#         conn, addr = server.accept()
#         AllconnectedComp[addr[1]]=[addr[0],conn]
#         conn.send(str(addr[1]).encode(FORMAT))
#         thread = threading.Thread(target=handle_client, args=(conn, addr))      
#         thread.start()
        
        # print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

# This is a broadcast function which listens for all broadcasted message from any client and sends all available chatrooms to the client
# def broadStart():
#     print(f"[LISTENING] Server is listening brodcasts on {BROADCASTADDR}")
#     while True:
#         message, addr = brodcast_server_socket.recvfrom(64)
  
#         message= message.decode(FORMAT)
#         message,Type= message.split(",")[0],message.split(",")[1]
#         print(message)
#         if len(message.split(":"))==2:

#             if message.split(":")[0]=="CONN":
#                 # try:
#                 connect_to_client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 connect_to_client_socket.connect((addr[0],int(message.split(":")[1])))

#                 # except:
#                 #     print("yoU WERE TRYING TO CONNECT TO AN ALREADY CONNECTION ")
            
#                 continue

        


#         print(message, Type)
#         # SendRoomsThread = threading.Thread(target=SendRooms, args=(senderIP,addr,Type))
#         # SendRoomsThread.start()
#         SendRooms(int(message),addr,Type)
# def SendRooms(ConnNumber,addr,Type):
#     print(addr)
#     if  ConnNumber and Type:
#         print(f"Sending Chat Rooms available to Client who Requested it with {addr[0]}")
#         if len(ChatRooms)==0:
#             AllconnectedComp[ConnNumber][1].send(str("Sorry there is no Chat ROOMS , Please create one by /CREATE").encode(FORMAT))
#         else:
#             AllconnectedComp[ConnNumber][1].send(str("Here are the available Rooms \n").encode(FORMAT))
#             for x in ChatRooms:
#                 message=x.name+","+ x.server_on+"\n"
#                 AllconnectedComp[ConnNumber][1].send(message.encode(FORMAT))
#             AllconnectedComp[ConnNumber][1].send(str("If you want to create a Chat Room for you you can also create one by /CREATE").encode(FORMAT))





