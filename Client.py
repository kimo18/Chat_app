import socket
import time
import threading
import sys


class Client:
    HEADER = 64
    Socketconn = ""
    BROADCAST_IP = "255.255.255.255"
    BROADCAST_PORT = 5972
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"
    DISCONNECT_FLAG = False
    MY_IP = socket.gethostbyname(socket.gethostname())
    server_IP = socket.gethostbyname(socket.gethostname())
    # JOINEDROOMS = []
    FT = True
    local_timestamp = 0
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_to_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_to_listen.bind((MY_IP, 0))
    # SETUP THE CLIENT THAT WOULD CONNECT TO THE LEADER SERVER
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # LISTEN TO ANSWERS FROM THE BROADCASTED MESSAGE
    Port_tobroadcast = client_to_listen.getsockname()[1]
    Recthread = threading.Thread()
    # boolians
    is_not_connected = True
    is_server_down = True
    is_started = False
    is_heartbeat_dead = True
    is_first_msg_sent = False

    def __init__(self):

        print("this is the port", self.Port_tobroadcast)
        # START THE THREAD THAT LISTENS FOR THE LEADER
        get_leaderIP_Thread = threading.Thread(target=self.GetServerIP)
        get_leaderIP_Thread.start()

        # BROADCAST THE MESSAGE TO THE LEADER SERVER
        heart_beat_thread = threading.Thread(target=self.send_client_heartbeat)
        heart_beat_thread.start()

    def broadcast(self, ip, port, message):
        # Send message on broadcast address
        MESSAGE = message+","+"Client"
        self.broadcast_socket.sendto(MESSAGE.encode(self.FORMAT), (ip, port))
        # time.sleep(2)

    def send(self, msg):
        message = msg.encode(self.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)
        # print(client.recv(64).decode(FORMAT))

    def NormReceiver(self, LserverIP, conn):
        self.client.connect((LserverIP, 5050))
        self.is_server_down = False

        while True:
            if self.DISCONNECT_FLAG:
                return
            self.client.settimeout(1)
            if self.is_server_down:
                print("server dowwwwwwwwn")
                self.FT = True
                break

            if not (self.FT):
                try:
                    msg = self.client.recv(64).decode(self.FORMAT)
                    if len(msg) > 0:

                        if '_' in msg:
                            time_stamp = msg.split('_')[0]
                            thread = threading.Thread(
                                target=self.check_precedence, args=(time_stamp, msg))
                            thread.start()

                        elif '?' in msg:
                            self.local_timestamp = int(msg.split("?")[0])
                            print(msg.split('?')[1], "\n")
                        else:
                            print(msg, "\n")
                except:
                    if self.is_server_down:
                        print("server dowwwwwwwwn")
                        self.FT = True
                        break
            else:
                print(self.FT)

                try:
                    self.Socketconn = self.client.recv(64).decode(self.FORMAT)
                except:
                    if self.is_server_down:
                        print("server dowwwwwwwwn")
                        self.FT = True
                        break
                print("THIS IS THE SOCK NUM", self.Socketconn)
                self.FT = False

    # WHEN THE SOCKET RECEVIES THE IP FROM THE SERVER IT CONNECTS WITH THE SERVER TCP

    def GetServerIP(self):
        global Recthread
        self.client_to_listen.listen()

        while True:
            conn = ''
            while self.is_server_down:
                conn, LServerIP = self.client_to_listen.accept()
                print("accepted", LServerIP)
                self.is_server_down = False

            # start to listen for messeages coming from tcp side
            if not (self.is_started) and not self.is_server_down:
                Recthread = threading.Thread(
                    target=self.NormReceiver, args=(LServerIP[0], conn))
                Recthread.start()
                self.is_started = True

            # conn.close()

# Send a heart beat to the server to check if it is alive or not (detect server crash)
    def send_client_heartbeat(self):
        while True:
            self.is_heartbeat_dead = True
            time.sleep(2)
            self.is_heartbeat_dead = False
            if self.DISCONNECT_FLAG:
                return
            try:
                self.send(f"{self.Port_tobroadcast}?HEARTBEAT")
            except:
                self.is_server_down = True
                self.is_started = False
                self.is_first_msg_sent = False
                if not self.FT:
                    print("We're currently performing a server exorcism to rid them of any evil spirits causing downtime. Hang tight, we'll have them back in no time!")

                while self.is_server_down:
                    to_broadcast_port = self.client_to_listen.getsockname()[1]
                    self.broadcast(self.BROADCAST_IP, self.BROADCAST_PORT,
                                   "CONN:"+str(to_broadcast_port))
                    time.sleep(0.5)

    def check_precedence(self, time_stamp, message):
        while True:
            if self.local_timestamp + 1 < int(time_stamp):
                time.sleep(0.5)
            else:
                self.local_timestamp += 1
                print(message)
                return

    # ---------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------

    while True:
        if is_heartbeat_dead:
            msg = input()
            if msg == DISCONNECT_MESSAGE:
                send(msg)
                DISCONNECT_FLAG = True
                broadcast_socket.close()

            elif len(msg) >= 2:
                if msg[:2] == "/A":
                    if FT or not is_first_msg_sent:
                        broadcast(BROADCAST_IP,
                                  BROADCAST_PORT, Socketconn)
                    else:
                        broadcast(BROADCAST_IP, BROADCAST_PORT,
                                  f"{server_IP}:{Port_tobroadcast}")
                elif msg[:2] == "/M":
                    local_timestamp += 1
                    send(f"{Port_tobroadcast}?{msg}")
                    is_first_msg_sent = True
                else:
                    if len(msg) >= 5:
                        if msg[:5] == "/JOIN":
                            send(f"{Port_tobroadcast}?{msg}")
                            is_first_msg_sent = True

                        else:
                            if len(msg) >= 7:
                                if msg[:7] == "/CREATE":
                                    send(
                                        f"{Port_tobroadcast}?{msg}")
                                    is_first_msg_sent = True

                                else:
                                    print("Not a valid Keyword\n")

    # if __name__ == "__main__":
    #     print(sys.argv)
    #     main(self)
