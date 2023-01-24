import socket
import time
import threading
import sys
import pickle


HEADER = 64
Socketconn = ""
BROADCASTIP = "255.255.255.255"
BROADCASTPORT = 5972
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "/DISCONNECT"
MYIP = socket.gethostbyname(socket.gethostname())
JOINEDROOMS = []
FT = True
broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
Recthread = threading.Thread()
# BOOLS
not_connected = True
serverdown = True
started = False


def broadcast(ip, port, message):
    # Create a UDP socket

    # while True:

    # Send message on broadcast address
    MESSAGE = message+","+"Client"
    broadcast_socket.sendto(MESSAGE.encode(FORMAT), (ip, port))
    # time.sleep(2)


def send(msg):
    global client
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    # print(client.recv(64).decode(FORMAT))


def NormReceiver(LserverIP, conn):
    global serverdown
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((LserverIP, 5050))
    serverdown = False

    global FT
    while True:

        client.settimeout(1)
        if serverdown:
            print("server dowwwwwwwwn")
            FT = True
            break

        if not (FT):
            try:
                msg = client.recv(64).decode(FORMAT)
                if len(msg) > 0:
                    print(msg, "\n")
            except:
                if serverdown:
                    print("server dowwwwwwwwn")
                    FT = True
                    break
        else:
            print(FT)
            global Socketconn
            try:
                Socketconn = client.recv(64).decode(FORMAT)
            except:
                if serverdown:
                    print("server dowwwwwwwwn")
                    FT = True
                    break
            print("THIS IS THE SOCK NUM", Socketconn)
            FT = False

# WHEN THE SOCKET RECEVIES THE IP FROM THE SERVER IT CONNECT WITH THE SERVER TCP


def GetServerIP():
    global not_connected
    global Recthread
    global serverdown
    global started
    client_to_listen.listen()
    while True:
        conn = ''
        while serverdown:
            conn, LServerIP = client_to_listen.accept()
            print("accepted", LServerIP)
            serverdown = False

        # START HERE TO listen from messeages coming from tcp Side
        if not (started) and not serverdown:
            Recthread = threading.Thread(
                target=NormReceiver, args=(LServerIP[0], conn))
            Recthread.start()
            started = True

        # conn.close()

# Send a heart beat to the server to check if it is available or not (detect server crash)


def client_heartbeat():
    global Recthread
    global get_leaderIP_Thread
    global started
    global serverdown
    while True:
        time.sleep(0.5)
        try:
            send("HEARTBEAT")
        except:
            serverdown = True
            started = False
            print("We're currently performing a server exorcism to rid them of any evil spirits causing downtime. Hang tight, we'll have them back in no time")

            while serverdown:
                Port_tobroadcast = client_to_listen.getsockname()[1]
                broadcast(BROADCASTIP, BROADCASTPORT,
                          "CONN:"+str(Port_tobroadcast))
                time.sleep(0.5)


# SETUP THE CLIENT THAT WOULD CONNECT TO THE LEADER SERVER
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ---------------------------------------------------------------------------------------

# LISTEN TO ANSWERS FROM THE BRODCASTED MESSAGE
client_to_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_to_listen.bind((MYIP, 0))
Port_tobroadcast = client_to_listen.getsockname()[1]
print("this is the port", Port_tobroadcast)
# START THE THREAD THAT LISTENS FOR THE LEADER
get_leaderIP_Thread = threading.Thread(target=GetServerIP)
get_leaderIP_Thread.start()
# -----------------------------------------------------------------------------------------

# BROADCAST THE MESSAGE TO THE LEADER SERVER

heart_beat_thread = threading.Thread(target=client_heartbeat)
heart_beat_thread.start()
# while serverdown:
#     print("Iam broadcasting")
#     broadcast(BROADCASTIP,BROADCASTPORT,"CONN:"+str(Port_tobroadcast))
#     time.sleep(0.5)

serverIP = socket.gethostbyname(socket.gethostname())
# --------------------------------------------------------------------------------------------


# send broadcast message over network so Leader answers


while True:

    mess = input()
    if mess == DISCONNECT_MESSAGE:
        send(mess)
        broadcast_socket.close()

    if len(mess) >= 2:
        if mess[:2] == "/A":
            broadcast(BROADCASTIP, BROADCASTPORT, Socketconn)
        elif mess[:2] == "/M":
            send(mess)
        else:
            if len(mess) >= 5:
                if mess[:5] == "/JOIN":
                    send(mess)
                else:
                    if len(mess) >= 7:
                        if mess[:7] == "/CREATE":
                            send(mess)
                        else:
                            print("Not a valid Keyword\n")

# send(DISCONNECT_MESSAGE)
