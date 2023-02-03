import socket
import threading
import sys
from ChatRoom import ChatRoom
import time
import json
import emoji


class Server:
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"
    is_leader = False
    is_participant = False
    server_ip = socket.gethostbyname(socket.gethostname())
    port = 0
    ADDR = (server_ip, 0)
    BROADCAST_ADDR = (server_ip, 5972)
    SERVERSERVERADDR = (server_ip, 6060)
    servers_list = []
    num_of_servers = 1
    chat_rooms = []
    list_of_connected_clients = {}
    leader_IP = None
    # list of booleans indicating the hp of each server(is alive)
    server_hp = []
    # Intializing broadcast server to listen to other nodes' requests
    broadcast_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_server_socket.bind(BROADCAST_ADDR)

    server_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    connect_to_server_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)

    # Intializing TCP server to listen for clients' requests/messages
    server_tolisten_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leaderserver_to_server_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, is_leader, port=5050):
        self.is_leader = is_leader == "True"
        self.port = int(port)
        # self.start_broadcast()
        self.ADDR = (self.server_ip, self.port)
        self.server_tolisten_socket.bind(self.ADDR)
        self.leaderserver_to_server_socket.bind((self.server_ip, 0))
        self.servers_list.append(
            f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}")
        self.num_of_servers = len(self.servers_list)
        threading.Thread(target=self.serverlisten).start()
        threading.Thread(target=self.send_heartbeat_message).start()
        # if leader server, then it listens for broadcasted messages from other servers
        if self.is_leader:
            self.leader_IP = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
            self.server_server_socket.bind(self.SERVERSERVERADDR)
            threading.Thread(target=self.ServerBroadListen).start()

        # if server not leader, then it broadcasts to the leader a message with its tcp port
        else:
            self.s_broadcast(
                6060, f"CONN:{self.leaderserver_to_server_socket.getsockname()[1]}")


# _________________________________________________________________________________________


    def handle_client(self, conn, addr):
        print(f"[NEW CLIENT CONNECTION]: {addr} connected.")
        port = ""
        connected = True
        # LOOPING UNTILL THE CLIENT SENDS THE DISCONNECT MESSAGE OR CLOSES THE TERMINAL
        while connected:
            try:
                msg_length = conn.recv(self.HEADER).decode(self.FORMAT)

            except ConnectionResetError as exception:
                connected = False
                if not (self.chat_rooms):
                    print(f"User {addr[0]}:{port} has left the chat room!")

                del self.list_of_connected_clients[f"{addr[0]}:{port}"]
                for chat_rooms in self.chat_rooms:
                    if chat_rooms.Leader == f"{addr[0]}:{port}":
                        if len(chat_rooms.users) == 1:
                            self.chat_rooms.remove(chat_rooms)
                            threading.Thread(target=self.form_replica).start()
                        else:
                            chat_rooms.users.remove(f"{addr[0]}:{port}")
                            chat_rooms.Leader = chat_rooms.users[0]
                            threading.Thread(target=self.form_replica).start()
                    elif f"{addr[0]}:{port}" in chat_rooms.users:
                        chat_rooms.users.remove(f"{addr[0]}:{port}")
                        threading.Thread(target=self.form_replica).start()

                msg_length = None
                conn.close()
                return

            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.FORMAT)

                print(f"Client with address {addr[0]} and port {msg.split('?')[0]} is Alive")
                client_port = msg.split("?")[0]
                port = client_port
                msg = msg.split("?")[1]

                # Keyword to send messages from clients to other clients in the same chatroom
                if msg[:2] == "/M":
                    message = msg.split(" ")
                    if len(message) > 1:
                        roomname = message[1]
                        for room in self.chat_rooms:
                            if room.name == roomname and (f"{addr[0]}:{client_port}" in room.users):
                                room.sequencer += 1
                                threading.Thread(
                                    target=self.form_replica).start()
                                message = f"{room.sequencer}_{addr[0]} sent: {message[2]}".encode(
                                    self.FORMAT)
                                print("this is the users in the room {room.users}")
                                for socket_num in room.users:

                                    if not (f"{addr[0]}:{client_port}" == socket_num):
                                        if len(message) > 2:
                                            self.list_of_connected_clients[socket_num][1].send(
                                                message)

                # keyword to create a chat room and add the user who created it to it
                if msg[:7] == "/CREATE":
                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg) > 8:
                        user = f"{addr[0]}:{client_port}"
                        self.CreateRoom(user, msg[8:], self.server_ip)
                        conn.send(
                            f"Room with name {msg[8:]} has been created".encode(self.FORMAT))
                        threading.Thread(target=self.form_replica).start()
                        try:
                            client_data = self.list_of_connected_clients[addr[1]]
                            del self.list_of_connected_clients[addr[1]]
                            self.list_of_connected_clients[user] = client_data

                        except:
                            pass

                        for key, value in self.list_of_connected_clients.items():
                            if not (key == addr[1]):
                                value[1].send(
                                    f"A new room named {msg[8:]} was created by User {addr[0]}".encode(self.FORMAT))

                    else:
                        conn.send("Please Specify the name of the chatroom you want to create".encode(
                            self.FORMAT))
                # CLIENT SEND A MESSAGE TO JOIN AN EXISTING CHAT ROOM
                if msg[:5] == "/JOIN":

                    # WE NEED TO CHECK IF THE CLIENT SEND A MESSAGE WITHOUT NAME OF THE CHATROOM OR NOT
                    if len(msg) > 6:
                        user = f"{addr[0]}:{client_port}"
                        room = self.RoomSearch(msg[6:])
                        if not (room == None):
                            room.add_user(f"{addr[0]}:{client_port}")
                            threading.Thread(target=self.form_replica).start()
                            conn.send(
                                f"{room.sequencer}?You have joined {room.name} chatroom".encode(self.FORMAT))
                        try:
                            client_data = self.list_of_connected_clients[addr[1]]
                            del self.list_of_connected_clients[addr[1]]
                            self.list_of_connected_clients[user] = client_data

                        except:
                            pass

                            
                        else:
                            conn.send(
                                f"There is no chatroom with name: {msg[6:]}".encode(self.FORMAT))

                    else:
                        conn.send(
                            "Please Specify the name of the chatroom you want to join".encode(self.FORMAT))

                #  CHECK FOR THE DISCONNECT MESSAGE
                if msg == self.DISCONNECT_MESSAGE:
                    connected = False

                
        conn.close()

    def CreateRoom(self, user, name, server_iP):
        newChatRoom = ChatRoom(name, server_iP)
        newChatRoom.add_user(user)
        newChatRoom.set_leader(user)
        self.chat_rooms.append(newChatRoom)

    def RoomSearch(self, chatroom_name):
        for room in self.chat_rooms:
            if room.name == chatroom_name:
                return room
        return None

    def start(self):
        self.server_tolisten_socket.listen()
        print(
            f"[LISTENING] Server is listening on {self.server_ip, self.port}")
        # we accept any connection , then we create a new thread for this connection so we can communicate with it using handle_client function
        while True:
            conn, addr = self.server_tolisten_socket.accept()
            self.list_of_connected_clients[addr[1]] = [addr[0], conn]
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

# _________________________________________________________________________________________
#  server receive from other server

    def server_recv(self, conn, addr):
        while True:
            try:
                messagelen = conn.recv(64)
            except ConnectionResetError as exception:
                return
            message = ""

            try:
                messagelen = json.loads(messagelen.decode(self.FORMAT))
                message = conn.recv(messagelen)

            except:
                message = conn.recv(len(messagelen.decode(self.FORMAT)))

            if len(message) > 0:
                try:
                    message = json.loads(message.decode(self.FORMAT))
                    print('message content: ', message)

                    if 'Type' not in message.keys():
                        self.dic_to_room(message['chat_rooms'])
                        self.servers_list = message['servers_list']
                        self.leader_IP = message['leader_IP']
                        self.num_of_servers = len(self.servers_list)

                        if message:
                            print(
                                f"[LIST OF CHAT ROOMS: ] {self.chat_rooms} \n [LIST OF SERVERS: ] {self.servers_list}, their number is {self.num_of_servers} \n and leader server is {self.leader_IP}")
                    else:
                        threading.Thread(target=self.forward_election_message, args=[
                                         message,]).start()

                except:
                    # change the server's hp to 'True' when the leader server receives the hearbeat
                    message = message.decode(self.FORMAT)
                    port = message.split(":")[1]

                    for i, ip in enumerate(self.server_hp):
                        if ip[0] == f"{addr[0]}:{port}":
                            self.server_hp[i] = (ip[0], True)
                            print("booooooga", self.server_hp)

###########################################################################################################################
# function used to start server broadcasts so that its actively listening for incoming nodes' requests to join the system #
###########################################################################################################################

    def start_broadcast(self):
        print(
            f"[BROADCAST ACTIVE] Server is listening for broadcasts on address {self.BROADCAST_ADDR}")
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
            try:
                self.SendRooms(int(message), addr, Type)
            except:
                self.SendRooms(message, addr, Type)

########################################################
# Send heartbeat message from servers to leader server #
########################################################
    def send_heartbeat_message(self):
        recevied = False
        while not recevied:
            if self.leader_IP:
                recevied = True

        leader_IP, leader_port = self.leader_IP.split(
            ":")[0], int(self.leader_IP.split(":")[1])
        self.connect_to_server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server_socket.connect((leader_IP, leader_port))

        while True:
            if not self.is_leader and self.leader_IP:
                time.sleep(2)
                try:
                    message_to_send = f"HEARTBEAT:{self.leaderserver_to_server_socket.getsockname()[1]}"
                    self.connect_to_server_socket.send(str(len(message_to_send)).encode(
                        self.FORMAT)+b' '*(self.HEADER-len(str(len(message_to_send)).encode(self.FORMAT))))
                    self.connect_to_server_socket.send(
                        message_to_send.encode(self.FORMAT))
                # maybe we'll start leader election here
                except:
                    self.servers_list.remove(self.leader_IP)
                    self.leader_IP = None
                    time.sleep(1)
                    print(emoji.emojize(
                        ":red_exclamation_mark: :red_exclamation_mark: LEADER SERVER CRASHED :red_exclamation_mark: :red_exclamation_mark:"))
                    self.start_election()


# send available chat rooms

    def SendRooms(self, ConnNumber, addr, Type):
        print(addr)
        if ConnNumber and Type and self.is_leader:
            print(
                f"Sending available chat rooms to client at address {addr[0]}")
            if len(self.chat_rooms) == 0:
                self.list_of_connected_clients[ConnNumber][1].send(str(
                    "Sorry, no chat rooms available, please create one by using /CREATE").encode(self.FORMAT))
            else:
                self.list_of_connected_clients[ConnNumber][1].send(
                    str("Here are the available chat rooms \n").encode(self.FORMAT))
                for room in self.chat_rooms:
                    message = room.name+"," + room.server_on+"\n"
                    self.list_of_connected_clients[ConnNumber][1].send(
                        message.encode(self.FORMAT))
                self.list_of_connected_clients[ConnNumber][1].send(str(
                    "If you want to create a chat room, you can by using /CREATE").encode(self.FORMAT))


# server broadcast to other servers

    def s_broadcast(self, port, message):
        MESSAGE = message + "," + "Server"
        self.server_server_socket.sendto(MESSAGE.encode(
            self.FORMAT), ("255.255.255.255", port))


# send to other server info


    def ServerBroadListen(self):
        print(
            f"[LISTENING] Server is listening for broadcasts from servers on {self.SERVERSERVERADDR}")
        while True:
            message, addr = self.server_server_socket.recvfrom(self.HEADER)
            message = message.decode(self.FORMAT)
            message, Type = message.split(",")[0], message.split(",")[1]
            newServer = f"{addr[0]}:{int(message.split(':')[1])}"
            # check if the broadcasted message is not in the server list
            if not (newServer in self.servers_list):
                self.server_hp.append((newServer, False))
                self.servers_list.append(newServer)
                self.num_of_servers = len(self.servers_list)
                self.form_ring()
                threading.Thread(target=self.ttl_set_remove,
                                 args=(newServer, 5)).start()

            if len(message.split(":")) == 2:
                if message.split(":")[0] == "CONN":
                    replica = {
                        "chat_rooms": self.chat_rooms,
                        "servers_list": self.servers_list,
                        "leader_IP": self.leader_IP
                    }
                    self.send_updates(json.dumps(replica))

    def begin(self):
        thread = threading.Thread(target=self.start)
        broadthread = threading.Thread(target=self.start_broadcast)
        broadthread.start()
        thread.start()


#######################
# For leader election #
#######################


    def form_ring(self):

        ports = [member.split(":")[1] for member in self.servers_list]
        ip_addresses = [socket.inet_aton(member.split(":")[0])
                        for member in self.servers_list]
        index = [i[0]
                 for i in sorted(enumerate(ip_addresses), key=lambda x:x[1])]
        self.servers_list = [f"{socket.inet_ntoa(ip)}:{port}" for _, ip, port in sorted(
            zip(index, ip_addresses, ports))]
        print("[RING IS FORMED]", self.servers_list)

    def get_neighbour(self, direction='left'):
        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.servers_list.index(
            current_node) if current_node in self.servers_list else -1
        if current_node_index != -1:
            if direction == 'left':
                if current_node_index + 1 == len(self.servers_list):
                    return self.servers_list[0]
                else:
                    return self.servers_list[current_node_index + 1]
            else:
                if current_node_index == 0:
                    return self.servers_list[len(self.servers_list) - 1]
                else:
                    return self.servers_list[current_node_index - 1]
        else:
            return None


# this function will be used by each node in the ring to start the election
# a node will construct its election msg and then pass it down to its neighbour


    def start_election(self):
        print("Leader election started..........")
        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.servers_list.index(current_node)
        message = {"Type": "ELECT",
                   "PID": current_node_index,
                   "is_Leader": False}
        message = json.dumps(message)
        neighbour = self.get_neighbour()
        ip, port = neighbour.split(":")[0], int(neighbour.split(":")[1])
        ring_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ring_socket.connect((ip, port))
        time.sleep(1)
        to_send_len = json.dumps(len(message))
        print("start election, message dumps is: ", json.dumps(message))
        print("start election, message loads is: ", json.loads(message))
        print("LENGTH IS: ", len(message))
        ring_socket.send(to_send_len.encode(self.FORMAT))
        ring_socket.send(message.encode(self.FORMAT))


# this function will be used by each node to forward election msgs around the ring
# either one of 3 cases is true for a given msg
# a node receives an election msg with a pid lower than its own and its not a is_participant,
    # it then adds its pid to a new msg and marks itself as is_participant
# a node receives an election msg with a pid bigger than its own and its not a is_participant,
    # it passes the msg down to the next node without updating the pid and marks itself as is_participant
# a node receives an election msg with its own pid,
    # it understands that it has become the new leader and hence sends out a broadcast msg to notify all nodes


    def forward_election_message(self, neighbour_msg):
        print("Forwarding election message to neighbour...........")
        time.sleep(2)
        neighbour = self.get_neighbour()
        ip, port = neighbour.split(':')[0], neighbour.split(":")[1]
        print(f"this is my neighbour {ip}  {port}")
        # creating a TCP socket to be used for passing election msgs around the ring
        ring_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ring_socket.connect((ip, int(port)))

        current_node = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
        current_node_index = self.servers_list.index(current_node)

        if neighbour_msg['is_Leader'] and not (neighbour_msg['PID'] == current_node_index):
            self.is_participant = False
            self.leader_IP = self.servers_list[neighbour_msg['PID']]

            leader_IP, leader_port = self.leader_IP.split(
                ":")[0], int(self.leader_IP.split(":")[1])
            self.connect_to_server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.connect_to_server_socket.connect((leader_IP, leader_port))

            to_send_len = json.dumps(len(json.dumps(neighbour_msg)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(neighbour_msg).encode(self.FORMAT))

        elif neighbour_msg['PID'] == current_node_index:
            # check if leader is receiving his own msg for the second time, so mark him as the leader & terminate
            if neighbour_msg['is_Leader'] == True:
                self.is_leader = True
                self.leader_IP = f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"
                print(emoji.emojize(
                    ":woman_dancing: :fire: I HAVE BEEN ELECTED THE NEW LEADER :fire: :woman_dancing:"))
                self.server_server_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM)
                self.server_server_socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.server_server_socket.bind(self.SERVERSERVERADDR)
                threading.Thread(target=self.ServerBroadListen).start()
                return
            else:
                print("[Received my own PID, I should be the leader!!]")
                new_election_message = {
                    "Type": "ELECT",
                    "PID": current_node_index,
                    "is_Leader": True
                }
                # mark self as no longer a participant and send new election message to left neighbour
                self.is_participant = False

                to_send_len = json.dumps(len(json.dumps(new_election_message)))
                ring_socket.send(to_send_len.encode(self.FORMAT))
                ring_socket.send(json.dumps(
                    new_election_message).encode(self.FORMAT))

        elif neighbour_msg['PID'] < current_node_index:
            # update msg with own PID & set self as is_participant
            new_election_message = {
                "Type": "ELECT",
                "PID": current_node_index,
                "is_Leader": False
            }
            self.is_participant = True
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            to_send_len = json.dumps(len(json.dumps(new_election_message)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(
                new_election_message).encode(self.FORMAT))

        elif neighbour_msg['PID'] > current_node_index:
            print(
                "[Received PID bigger than mine, passing msg down, no update needed!!]")
            # set self as participant and pass msg to next neighbour w/o updating PID
            self.is_participant = True
            to_send_len = json.dumps(len(json.dumps(neighbour_msg)))
            to_send_len = json.dumps(len(json.dumps(neighbour_msg)))
            ring_socket.send(to_send_len.encode(self.FORMAT))
            ring_socket.send(json.dumps(
                neighbour_msg).encode(self.FORMAT))

    def ttl_set_remove(self, server, ttl):
        while True:
            time.sleep(ttl)
            self.detect_crash(server)

    def detect_crash(self, server):
        for i, ip in enumerate(self.server_hp):
            if ip[0] == server:
                if not ip[1]:
                    self.servers_list.remove(server)
                    self.server_hp.remove((ip[0], ip[1]))
                    self.form_ring()
                    replica = {
                        "chat_rooms": self.chat_rooms,
                        "servers_list": self.servers_list,
                        "leader_IP": self.leader_IP
                    }
                    self.send_updates(json.dumps(replica))
                    self.send_updates(json.dumps(replica))

                else:
                    self.server_hp[i] = (ip[0], False)

    def send_updates(self, to_send):
        for ip_port in self.servers_list:
            if not (ip_port == f"{self.server_ip}:{self.leaderserver_to_server_socket.getsockname()[1]}"):
                connect_to_server_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                connect_to_server_socket.connect(
                    (ip_port.split(":")[0], int(ip_port.split(":")[1])))
                # sending the chat room replica to the newly connected server(s)
                to_send_len = json.dumps(len(to_send))
                connect_to_server_socket.send(to_send_len.encode(self.FORMAT))
                connect_to_server_socket.send(to_send.encode(self.FORMAT))
                to_send_len = json.dumps(len(to_send))
                connect_to_server_socket.send(to_send_len.encode(self.FORMAT))
                connect_to_server_socket.send(to_send.encode(self.FORMAT))

    def form_replica(self):
        replica = {
            "chat_rooms":  self.room_to_dict(),
            "servers_list": self.servers_list,
            "leader_IP": self.leader_IP}
        self.send_updates(json.dumps(replica))

    def room_to_dict(self):
        room_dict = {}
        for i, room in enumerate(self.chat_rooms):
            room_dict[f"{i}_name"] = room.name
            room_dict[f"{i}_server_on"] = room.server_on
            room_dict[f"{i}_users"] = room.users
            room_dict[f"{i}_Leader"] = room.Leader
            room_dict[f"{i}_messages"] = room.messages
            room_dict[f"{i}_sequencer"] = room.sequencer
        return room_dict

    def dic_to_room(self, dict_room):
        self.chat_rooms = []
        if not dict_room == []:
            for i in range(0, len(dict_room.keys()), 6):
                x = ChatRoom(dict_room[list(dict_room)[i]],
                             dict_room[list(dict_room)[i+1]])
                x.users = dict_room[list(dict_room)[i+2]]
                x.Leader = dict_room[list(dict_room)[i+3]]
                x.messages = dict_room[list(dict_room)[i+4]]
                x.sequencer = dict_room[list(dict_room)[i+5]]
                self.chat_rooms.append(x)


def main(is_leader, port):
    our_server = Server(is_leader, port)
    print(our_server.port, our_server.is_leader)
    print("[STARTING] server is starting...")
    our_server.begin()


if __name__ == "__main__":
    print(sys.argv)
    main(sys.argv[1], sys.argv[2])
