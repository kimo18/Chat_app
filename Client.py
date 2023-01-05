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

# BOOLS
not_connected=True

def broadcast(ip,port,message):
    # Create a UDP socket
    
    # while True:

    # Send message on broadcast address
    MESSAGE = message+","+"Client"
    broadcast_socket.sendto(MESSAGE.encode(FORMAT), (ip, port))
    # time.sleep(2)
def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    # print(client.recv(64).decode(FORMAT))

def NormReceiver(LserverIP):
    client.connect((LserverIP,5050))
    global FT
    while True:

        if not(FT):
            print(client.recv(64).decode(FORMAT),"\n")
        else:
            global Socketconn
            Socketconn= client.recv(64).decode(FORMAT)    
            print(Socketconn)  
            FT=False 

# WHEN THE SOCKET RECEVIES THE IP FROM THE SERVER IT CONNECT WITH THE SERVER TCP
def GetServerIP():
    global not_connected
    started = False
    client_to_listen.listen()
    while not_connected:
        conn, LServerIP = client_to_listen.accept()
        print("accepted")

        # START HERE TO listen from messeages coming from tcp Side
        if not(started):
            Recthread= threading.Thread(target=NormReceiver,args=(LServerIP[0],))
            Recthread.start()
            started =True
        
        not_connected=False
        conn.close()

# SETUP THE CLIENT THAT WOULD CONNECT TO THE LEADER SERVER 
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ---------------------------------------------------------------------------------------

# LISTEN TO ANSWERS FROM THE BRODCASTED MESSAGE
client_to_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_to_listen.bind((MYIP,0))
Port_tobroadcast=client_to_listen.getsockname()[1]
print("this is the port",Port_tobroadcast)
# START THE THREAD THAT LISTENS FOR THE LEADER
get_leaderIP_Thread=threading.Thread(target=GetServerIP)
get_leaderIP_Thread.start()
#-----------------------------------------------------------------------------------------

# BROADCAST THE MESSAGE TO THE LEADER SERVER 
while not_connected:
    print("Iam broadcasting")
    broadcast(BROADCASTIP,BROADCASTPORT,"CONN:"+str(Port_tobroadcast))
    time.sleep(0.5)

serverIP = socket.gethostbyname(socket.gethostname())
#--------------------------------------------------------------------------------------------




  



# send broadcast message over network so Leader answers



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