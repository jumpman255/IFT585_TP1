import sys
import socket
import os
import math
import pickle

IP = "127.0.0.1"
PORT = 9000
BUFFER_SIZE = 1
WINDOW_SIZE = 4


class Packet:
    def __init__(self, seq, data, last):
        self.seq = seq
        self.data = data
        self.last = last


class Client:
    def __init__(self, socket):
        self.socket = socket

    def send(self, filePath):
        lastPck = 0
        lastAckPck = 0
        fileSize = os.path.getsize(filePath)
        totalPck = math.ceil(fileSize / BUFFER_SIZE)  
        sentPcks = []

        with open(filePath, 'rb') as f:
            while True:
                # Envoyer le data
                while lastPck - lastAckPck < WINDOW_SIZE and lastPck < totalPck:
                    data = f.read(BUFFER_SIZE)

                    packet = Packet(lastPck, data, True if lastPck == totalPck - 1 else False)

                    # pickle permet de serialiser l'objet
                    self.socket.sendto(pickle.dumps(packet), (IP, PORT))
                    sentPcks.append(packet)

                    lastPck += 1

                # Recevoir le data
                try:
                    self.socket.settimeout(10)
                    packet, _ = self.socket.recvfrom(1024)
                    
                    pckSeq = int(packet)
                    
                    if pckSeq == totalPck:
                        break

                    lastAckPck = max(lastAckPck, pckSeq)
                
                except socket.timeout:
                    # Renvoyer les packet deja envoyes mais qui n'ont pas ete ack'd.
                    for i in range(lastAckPck, lastPck):
                        packet = pickle.dumps(sentPcks[i])
                        self.socket.sendto(packet, (IP, PORT))


class Server:
    def __init__(self, socket):
        self.socket = socket
    
    def listen(self):
        self.socket.bind((IP, PORT))
        waitingFor = 0

        while True:
            packet, address = self.socket.recvfrom(1200)
            packet = pickle.loads(packet)

            if packet.seq == waitingFor:
                waitingFor += 1

                with open("server.txt", "a+b") as f:
                    f.write(packet.data)

            self.socket.sendto(str.encode(str(waitingFor)), address)


socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
if sys.argv[1] == 'c':
    client = Client(socket)
    client.send("client.txt")
elif sys.argv[1] == 's':
    server = Server(socket)
    server.listen()