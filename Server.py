import socket
import threading
import pickle
import sys
from ChatRoom import ChatRoom
import time
import json


class Server:
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    is_leader = False
    participant = False
    server_ip = socket.gethostbyname(socket.gethostname())
    port = 0
    ADDR = (server_ip, 0)
    BROADCASTADDR = (server_ip, 5972)
    SERVERSERVERADDR = (server_ip, 6060)
    max_connections = 0
    server_dic = []
    current_connections = 0
    number_servers = 1
    chat_rooms = []
    all_connected_client = {}
    Ring = []
    leaderIP = None
    # list of booleans indicating the hp of the servers(is alive)
    server_hp = []
    # Intializing broadcast server to listen from other componenets
    broadcast_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_server_socket.bind(BROADCASTADDR)

    server_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # server_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Intializing TCP Server to listen from Clients messages
    server_tolisten_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leaderserver_to_server_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, is_leader, port=5050, max_connections=5):
        self.is_leader = is_leader == "True"
        self.port = int(port)
        # self.start_broadcast()
        self.ADDR = (self.server_ip, self.port)
        self.server_tolisten_socket.bind(self.ADDR)
        self.max_connections = max_connections
        self.leaderserver_to_server_socket.bind((self.server_ip, 0))
        self.server_dic.append(
            f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}")
        self.number_servers = len(self.server_dic)
        threading.Thread(target=self.serverlisten).start()
        threading.Thread(target=self.send_heartbeat_message).start()

        # if you are the leader then you listen for the broadcasted messages from the other server
        if self.is_leader:
            self.leaderIP = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
            self.server_server_socket.bind(self.SERVERSERVERADDR)
            threading.Thread(target=self.ServerBroadListen).start()

        # when you are not the leader you send to the leader a broadcast message with the tcp port you have
        else:
            self.s_broadcast(
                6060, f"CONN:{self.leaderserver_to_server_socket.getsockname()[1]}")


# _________________________________________________________________________________________

    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")

        connected = True
        # LOOPING UNTILL THE CLIENT SENDS THE DISCONNECT MESSAGE TO CLOSE THE CONNECTION
        while connected:
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.FORMAT)

                # Send Messages from clients to other clients in same chatroom
                if msg[:2] == "/M":
                    Message = msg.split(" ")
                    if len(Message) > 1:
                        roomname = Message[1]
                        for x in self.chat_rooms:
                            if x.name == roomname and (addr[1] in x.users):
                                for socketnum in x.users:
                                    if not (addr[1] == socketnum):
                                        if len(Message) > 2:
                                            self.all_connected_client[socketnum][1].send(
                                                Message[2].encode(self.FORMAT))

                # CREATE A CHAT ROOM AND ADD THE USER WHO CREATED IT
                if msg[:7] == "/CREATE":
                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg) > 8:
                        self.CreateRoom(addr[1], msg[8:], self.server_ip)
                        conn.send(
                            f"Room with name {msg[8:]} is created".encode(self.FORMAT))
                        for key, value in self.all_connected_client.items():
                            print(key, value)
                            if not (key == addr[1]):
                                value[1].send(
                                    f"A new Room named {msg[8:]} was Created by User {addr[0]}".encode(self.FORMAT))

                    else:
                        conn.send("Please Specify the name of the chatroom you want to create".encode(
                            self.FORMAT))
                # CLIENT SEND A MESSAGE TO JOIN AN EXISTING CHAT ROOM
                if msg[:5] == "/JOIN":
                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg) > 6:
                        room = self.RoomSearch(msg[6:])
                        if not (room == None):
                            room.add_user(addr[1])
                            conn.send(
                                F"You have joined {room.name} chatroom".encode(self.FORMAT))
                        else:
                            conn.send(
                                F"There is no chatroom with name: {room.name}".encode(self.FORMAT))

                    else:
                        conn.send(
                            "Please Specify the name of the chatroom you want to join".encode(self.FORMAT))
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

    def CreateRoom(self, user, name, server_iP):
        newChatRoom = ChatRoom(name, server_iP)
        newChatRoom.add_user(user)
        newChatRoom.set_leader(user)
        self.chat_rooms.append(newChatRoom)


# _________________________________________________________________________________________

    def RoomSearch(self, chatroom_name):
        for x in self.chat_rooms:
            if x.name == chatroom_name:
                return x
        return None


# _________________________________________________________________________________________

    def start(self):
        self.server_tolisten_socket.listen()
        print(
            f"[LISTENING] Server is listening on {self.server_ip, self.port}")
        # we accept any connection , then we create a new thread for this connection so we can communicate with it by handle connection function
        while True:
            conn, addr = self.server_tolisten_socket.accept()
            self.all_connected_client[addr[1]] = [addr[0], conn]
            conn.send(str(addr[1]).encode(self.FORMAT))
            thread = threading.Thread(
                target=self.handle_client, args=(conn, addr))
            thread.start()


# _________________________________________________________________________________________
#  server listen from other servers

    def serverlisten(self):
        self.leaderserver_to_server_socket.listen()
        print("Heloooooooooooooooooooooo",
              self.leaderserver_to_server_socket.getsockname())

        while True:
            conn, addr = self.leaderserver_to_server_socket.accept()
            thread = threading.Thread(
                target=self.server_recv, args=(conn, addr))
            thread.start()
            print("bttts", addr)


# _________________________________________________________________________________________
#  server receive from other server

    def server_recv(self, conn, addr):
        while True:
            messagelen = conn.recv(64)
            message = ""
            try:
                messagelen = json.loads(messagelen.decode(self.FORMAT))
                message = conn.recv(messagelen)
                print("msg len in recv: ", messagelen)
                print("msg in recv: ", message)

            except:
                message = conn.recv(len(messagelen.decode(self.FORMAT)))

            if len(message) > 0:
                try:
                    message = json.loads(message.decode(self.FORMAT))
                    print("pickled")
                    print('message content: ', message)

                    if 'Type' not in message.keys():
                        self.chat_rooms = message['chat_rooms']
                        self.server_dic = message['servers_list']
                        self.leaderIP = message['leader_IP']
                        self.number_servers = len(self.server_dic)
                        if message:
                            print(
                                f" this is the chat rooms{self.chat_rooms} \n [LIST OF SERVERS: ] {self.server_dic} with number of servers = {self.number_servers} \n and leader server is {self.leaderIP}")
                    else:
                        print("inside else for forward election msg")
                        self.forward_election_message(message)

                except:
                    # change the server's hp to 'True' when the leader server receives the hearbeat
                    print("Iam in")
                    message = message.decode(self.FORMAT)
                    port = message.split(":")[1]
                    for i, ip in enumerate(self.server_hp):
                        if ip[0] == f"{addr[0]}:{port}":

                            self.server_hp[i] = (ip[0], True)
                            print("booooooga", self.server_hp)

                    # _________________________________________________________________________________________

    def start_broadcast(self):
        print(
            f"[LISTENING] Server is listening for brodcasts on {self.BROADCASTADDR}")
        while True:
            message, addr = self.broadcast_server_socket.recvfrom(64)

            message = message.decode(self.FORMAT)
            message, Type = message.split(",")[0], message.split(",")[1]
            print(message)
            if len(message.split(":")) == 2:

                if message.split(":")[0] == "CONN":
                    # try:
                    if self.is_leader:
                        print(f"Leader with address: {self.server_ip}")
                        connect_to_client_socket = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        connect_to_client_socket.connect(
                            (addr[0], int(message.split(":")[1])))

                    # except:
                    #     print("yoU WERE TRYING TO CONNECT TO AN ALREADY CONNECTION ")

                    continue

            print(message, Type)
            # SendRoomsThread = threading.Thread(target=SendRooms, args=(senderIP,addr,Type))
            # SendRoomsThread.start()
            self.SendRooms(int(message), addr, Type)


# _________________________________________________________________________________________

# Send heartbeat message from servers to leader server

    def send_heartbeat_message(self):
        recevied = False
        while not recevied:
            if self.leaderIP:
                recevied = True

        leader_IP, leader_port = self.leaderIP.split(
            ":")[0], int(self.leaderIP.split(":")[1])
        connect_to_server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        connect_to_server_socket.connect((leader_IP, leader_port))

        while True:
            if not self.is_leader and self.leaderIP:
                time.sleep(2)
                try:
                    message_to_send = f"HEARTBEAT:{self.leaderserver_to_server_socket.getsockname()[1]}"
                    connect_to_server_socket.send(str(len(message_to_send)).encode(
                        self.FORMAT)+b' '*(self.HEADER-len(str(len(message_to_send)).encode(self.FORMAT))))
                    connect_to_server_socket.send(
                        message_to_send.encode(self.FORMAT))
                # maybe we'll start leader election here
                except:
                    print("LEADER IP: ", self.leaderIP)
                    print("DICTIONARY", self.server_dic)
                    self.server_dic.remove(self.leaderIP)
                    self.leaderIP = None
                    time.sleep(1)
                    print(":x: :x: LEADER SERVER CRASHED :x: :x:")
                    self.start_election()


# _________________________________________________________________________________________


    def SendRooms(self, ConnNumber, addr, Type):
        print(addr)
        if ConnNumber and Type:
            print(
                f"Sending available chat rooms to client at address {addr[0]}")
            if len(self.chat_rooms) == 0:
                self.all_connected_client[ConnNumber][1].send(str(
                    "Sorry, no chat rooms available, please create one by /CREATE").encode(self.FORMAT))
            else:
                self.all_connected_client[ConnNumber][1].send(
                    str("Here are the available chat rooms \n").encode(self.FORMAT))
                for x in self.chat_rooms:
                    message = x.name+"," + x.server_on+"\n"
                    self.all_connected_client[ConnNumber][1].send(
                        message.encode(self.FORMAT))
                self.all_connected_client[ConnNumber][1].send(str(
                    "If you want to create a chat room, you can by /CREATE").encode(self.FORMAT))


# _________________________________________________________________________________________
# server broadcast to other server

    def s_broadcast(self, port, message):

        MESSAGE = message+","+"Server"
        self.server_server_socket.sendto(MESSAGE.encode(
            self.FORMAT), ("255.255.255.255", port))


# _________________________________________________________________________________________
# send to other server info


    def ServerBroadListen(self):
        print(
            f"[LISTENING] Server is listening brodcasts from Servers on {self.SERVERSERVERADDR}")
        while True:
            message, addr = self.server_server_socket.recvfrom(self.HEADER)
            message = message.decode(self.FORMAT)
            message, Type = message.split(",")[0], message.split(",")[1]
            newServer = f"{addr[0]}:{int(message.split(':')[1])}"
            # check if the broadcasted message is not in the server dic
            if not (newServer in self.server_dic):
                self.server_hp.append((newServer, False))
                self.server_dic.append(newServer)
                self.number_servers = len(self.server_dic)
                self.form_ring()
                threading.Thread(target=self.ttl_set_remove,
                                 args=(newServer, 5)).start()

            if len(message.split(":")) == 2:

                if message.split(":")[0] == "CONN":

                    replica = {
                        "chat_rooms": self.chat_rooms,
                        "servers_list": self.server_dic,
                        "leader_IP": self.leaderIP
                    }
                    self.send_updates(json.dumps(replica))
                    print("to send", len(replica))


# _________________________________________________________________________________________


    def begin(self):
        thread = threading.Thread(target=self.start)
        broadthread = threading.Thread(target=self.start_broadcast)
        broadthread.start()
        thread.start()


#######################
# For leader election #
#######################

    def form_ring(self):
        print("before", self.server_dic)

        ports = [member.split(":")[1] for member in self.server_dic]
        ips = [socket.inet_aton(member.split(":")[0])
               for member in self.server_dic]
        index = [i[0] for i in sorted(enumerate(ips), key=lambda x:x[1])]
        self.server_dic = [f"{socket.inet_ntoa(ip)}:{port}" for _, ip, port in sorted(
            zip(index, ips, ports))]
        print("after", self.server_dic)
        print("RingFormed")

    def get_neighbour(self, direction='left'):
        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.server_dic.index(
            current_node) if current_node in self.server_dic else -1
        if current_node_index != -1:
            if direction == 'left':
                if current_node_index + 1 == len(self.server_dic):
                    return self.server_dic[0]
                else:
                    return self.server_dic[current_node_index + 1]
            else:
                if current_node_index == 0:
                    return self.server_dic[len(self.server_dic) - 1]
                else:
                    return self.server_dic[current_node_index - 1]
        else:
            return None


# this function will be used by each node in the ring to start the election
# a node will construct its election msg and then pass it down to its neighbour


    def start_election(self):
        print("Leader election started..........")
        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.server_dic.index(current_node)
        message = {"Type": "ELECT",
                   "PID": current_node_index,
                   "is_leader": False}
        message = json.dumps(message)
        neighbour = self.get_neighbour()
        ip, port = neighbour.split(":")[0], int(neighbour.split(":")[1])
        ring_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ring_socket.connect((ip, port))
        to_send_len = json.dumps(len(message))
        print("start election, message dumps is: ", json.dumps(message))
        print("start election, message loads is: ", json.loads(message))
        print("LENGTH IS: ", len(message))
        ring_socket.send(to_send_len.encode(self.FORMAT))
        ring_socket.send(message.encode(self.FORMAT))


# this function will be used by each node to forward election msgs around the ring
# either one of 3 cases is true for a given msg
# a node receives an election msg with a pid lower than its own and its not a participant,
    # it then adds its pid to a new msg and marks itself as participant
# a node receives an election msg with a pid bigger than its own and its not a participant,
    # it passes the msg down to the next node without updating the pid and marks itself as participant
# a node receives an election msg with its own pid,
    # it understands that it has become the new leader and hence sends out a broadcast msg to notify all nodes


    def forward_election_message(self, neighbour_msg):
        print("Forwarding [ELECTION MESSAGE]...........")

        neighbour = self.get_neighbour()
        ip, port = neighbour.split(':')[0], neighbour.split(":")[1]

        # creating a TCP socket to be used for passing election msgs around the ring
        ring_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ring_socket.connect((ip, int(port)))
        ring_socket.connect((ip, int(port)))

        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.server_dic.index(current_node)

        if neighbour_msg['PID'] < current_node_index and not self.participant:
            # update msg with own PID & set self as participant
            new_election_message = {
                "Type": "ELECT",
                "PID": current_node_index,
                "is_Leader": False
            }
            self.participant = True
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(
                new_election_message).encode(self.FORMAT))

        elif neighbour_msg['PID'] > current_node_index and not self.participant:
            # set self as participant and pass msg to next neighbour w/o updating PID
            self.participant = True
            to_send_len = json.dumps(len(json.dumps(neighbour_msg)))
            to_send_len = json.dumps(len(json.dumps(neighbour_msg)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(
                neighbour_msg).encode(self.FORMAT))

        elif neighbour_msg['PID'] == current_node_index:
            # check if leader is receiving his own msg for the second time, so mark him as the leader & terminate
            if neighbour_msg['is_Leader'] == True:
                self.is_leader = True

            print("I HAVE BEEN ELECTED THE NEW LEADER :dancer: :dancer: :dancer:")
            new_election_message = {
                "PID": current_node_index,
                "is_Leader": True
            }
            # mark self as no longer a participant and send new election message to left neighbour
            self.participant = False
            self.leaderIP = self.server_ip
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(
                new_election_message).encode(self.FORMAT))

    def ttl_set_remove(self, server, ttl):
        while True:
            time.sleep(ttl)
            self.detect_crash(server)

    def detect_crash(self, server):

        for i, ip in enumerate(self.server_hp):
            if ip[0] == server:
                if not ip[1]:
                    self.server_dic.remove(server)
                    self.server_hp.remove((ip[0], ip[1]))
                    self.form_ring()
                    replica = {
                        "chat_rooms": self.chat_rooms,
                        "servers_list": self.server_dic,
                        "leader_IP": self.leaderIP
                    }
                    self.send_updates(json.dumps(replica))
                    self.send_updates(json.dumps(replica))

                else:
                    self.server_hp[i] = (ip[0], False)

    def send_updates(self, to_send):
        for ip_port in self.server_dic:

            print("what is the problema ", ip_port)
            if not (ip_port == f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"):
                connect_to_server_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                connect_to_server_socket.connect(
                    (ip_port.split(":")[0], int(ip_port.split(":")[1])))
                # sending here the chat room replica to the new connected server
                print("sending to Server", ip_port)
                to_send_len = json.dumps(len(to_send))
                connect_to_server_socket.send(to_send_len.encode(self.FORMAT))
                connect_to_server_socket.send(to_send.encode(self.FORMAT))
                to_send_len = json.dumps(len(to_send))
                connect_to_server_socket.send(to_send_len.encode(self.FORMAT))
                connect_to_server_socket.send(to_send.encode(self.FORMAT))


def main(is_leader, port):
    our_server = Server(is_leader, port)
    print(our_server.port, our_server.is_leader)
    print("[STARTING] server is starting...")
    our_server.begin()


if __name__ == "__main__":

    print(sys.argv)
    main(sys.argv[1], sys.argv[2])
