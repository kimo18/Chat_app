import socket
import time
import threading
import sys
import pickle
HEADER = 64
Socketconn=""
BROADCASTIP= "255.255.255.255"
BROADCASTPORT=5972
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "/DISCONNECT"
MYIP= socket.gethostbyname(socket.gethostname())
JOINEDROOMS=[]
FT=True
broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def broadcast(ip,port,message):
    # Create a UDP socket
    
    # while True:

    # Send message on broadcast address
    print(message)
    MESSAGE = message+","+"Client"
    broadcast_socket.sendto(MESSAGE.encode(FORMAT), (ip, port))
    # time.sleep(2)
    
    


serverPort=5050
serverIP = socket.gethostbyname(socket.gethostname())
ADDR = (serverIP, serverPort)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    # print(client.recv(64).decode(FORMAT))


  


def NormReceiver():
    global FT
    while True:

        if not(FT):
            print(client.recv(64).decode(FORMAT),"\n")
        else:
            global Socketconn
            Socketconn= client.recv(64).decode(FORMAT)    
            print(Socketconn)  
            FT=False
# send broadcast message over network so Leader answers




Recthread= threading.Thread(target=NormReceiver)
Recthread.start()

while FT:
    time.sleep(1)
broadcastmessage=  socket.gethostbyname(socket.gethostname())
broadthread= threading.Thread(target=broadcast, args=(BROADCASTIP, BROADCASTPORT,Socketconn))
broadthread.start()


while True:
    
    mess=input()
    if mess==DISCONNECT_MESSAGE:
        send(mess)
        broadcast_socket.close()


    if len(mess)>=2:
        if mess[:2]=="/A":
            broadcast(BROADCASTIP, BROADCASTPORT,Socketconn)
        elif mess[:2]=="/M":
            send(mess)    
        else:
            if len(mess)>=5:
                if mess[:5]=="/JOIN":
                    send(mess)
                else:    
                    if len(mess)>=7:    
                        if mess[:7]=="/CREATE":
                            send(mess)
                        else:
                            print("Not a valid Keyword\n")

#send(DISCONNECT_MESSAGE)