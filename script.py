import socket
import sys
import threading
import pickle
import os
import math
import random

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

WINDOW_SIZE = 10

# A CHANGER POUR -1 POUR ÉTAT NORMAL DU SCRIPT, CELA SERT SEULEMENT POUR TESTER
FAIL_PROBABILITY = -1


class Packet:
    def __init__(self, seq, data, last, filename, totalPck):
        self.seq = seq
        self.data = data
        self.last = last
        self.filename = filename
        self.totalPck = totalPck


class Client:
    def __init__(self, socket, isSender, file):
        self.socket = socket
        # Si le client send du data ou recoit du data.
        self.isSender = isSender
        self.file = file

    def file_transfer(self):
        if self.isSender:
            self.socket.sendto(str.encode("s"), (SERVER_IP, SERVER_PORT))
            packet, address = self.socket.recvfrom(1024)
            packet = packet.decode("utf-8")
            if packet == "ok":
                sender = Sender(self.socket, address)
                sender.send(self.file)
        else:
            receiver = Receiver(self.socket, (SERVER_IP, SERVER_PORT))
            self.socket.sendto(str.encode("r"), (SERVER_IP, SERVER_PORT))
            receiver.receive("FROM_SERVER_")


class Server:
    def __init__(self, socket):
        self.socket = socket

    def handle_request(self, data, client_address):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # le 0 indique qu'on va bind sur un port libre.
        s.bind((SERVER_IP, 0))
        data = data.decode("utf-8")

        if data == 's':
            receiver = Receiver(s, client_address)
            s.sendto(str.encode("ok"), client_address)
            receiver.receive("FROM_CLIENT_")
        elif data == 'r':
            sender = Sender(s, client_address)
            sender.send("server")

    def wait_for_client(self):
        self.socket.bind((SERVER_IP, SERVER_PORT))

        while True:
            packet, address = self.socket.recvfrom(1200)
            thread = threading.Thread(target=self.handle_request, args=(packet, address))
            thread.daemon = True
            thread.start()


class Sender:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address

    def send(self, file):
        lastPck = 0
        lastAckPck = 0
        fileSize = os.path.getsize(file)
        totalPck = math.ceil(fileSize / 50000)
        sentPcks = []

        with open(file, "rb") as f:
            while True:
                while lastPck - lastAckPck < WINDOW_SIZE and lastPck < totalPck:
                    data = f.read(50000)

                    packet = Packet(lastPck, data, lastPck == totalPck - 1, file, totalPck)

                    # pickle permet de serialiser l'objet
                    print("Sending packet {0}/{1} to {2}:{3}".format(lastPck + 1, totalPck, self.address[0], self.address[1]))
                    if random.uniform(0, 1) > FAIL_PROBABILITY:
                        self.socket.sendto(pickle.dumps(packet), self.address)

                    sentPcks.append(packet)

                    lastPck += 1

                # Recevoir le data
                try:
                    self.socket.settimeout(0.5)
                    packet, _ = self.socket.recvfrom(1024)

                    pckSeq = int(packet)

                    if pckSeq == totalPck:
                        print("Done sending all packets to {0}:{1}".format(self.address[0], self.address[1]))
                        break

                    lastAckPck = max(lastAckPck, pckSeq)

                except socket.timeout:
                    # Renvoyer les packet deja envoyes mais qui n'ont pas ete ack'd.
                    for i in range(lastAckPck, lastPck):
                        packet = pickle.dumps(sentPcks[i])
                        print("REsending packet {0}/{1} to {2}:{3}".format(i + 1, totalPck, self.address[0], self.address[1]))
                        if random.uniform(0, 1) > FAIL_PROBABILITY:
                            self.socket.sendto(packet, self.address)


class Receiver:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address

    def receive(self, prefix):
        waitingFor = 0

        done = False
        while not done:
            packet, address = self.socket.recvfrom(65000)
            packet = pickle.loads(packet)

            if packet.seq == waitingFor:
                print("Received packet {0}/{1} from {2}:{3}".format(waitingFor + 1, packet.totalPck, address[0], address[1]))

                waitingFor += 1

                with open(prefix + packet.filename, "a+b") as f:
                    f.write(packet.data)

                if packet.last:
                    print("Received all packets from {0}:{1}".format(address[0], address[1]))
                    done = True

            if random.uniform(0, 1) > FAIL_PROBABILITY:
                self.socket.sendto(str.encode(str(waitingFor)), address)


if sys.argv[1] == 's':
    server = Server(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    server.wait_for_client()
else:
    client = Client(
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
            True if sys.argv[2] == 's' else False,
            sys.argv[3] if len(sys.argv) == 4 else None)
    client.file_transfer()
