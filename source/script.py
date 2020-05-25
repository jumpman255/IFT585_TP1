import socket
import sys
import threading

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

class Packet:
    def __init__(self, seq, data, last, filename, _hash=None):
        self.seq = seq
        self.data = data
        self.last = last
        self.filename = filename
        self.hash = _hash

class Client:
    def __init__(self, socket, isSender):
        self.socket = socket
        # Si le client send du data ou recoit du data.
        self.isSender = isSender

    def file_transfer(self):
        if self.isSender:
            sender = Sender(self.socket, (SERVER_IP, SERVER_PORT))
            self.socket.sendto(str.encode("s"), (SERVER_IP, SERVER_PORT))
            # TODO - Meilleur gestion
            packet, _ = self.socket.recvfrom(1024)
            if packet == "ok":
                sender.send()
        else:
            receiver = Receiver(self.socket, (SERVER_IP, SERVER_PORT))
            # TODO - Meilleur gestion
            self.socket.sendto(str.encode("r"), (SERVER_IP, SERVER_PORT))
            receiver.receive()  

# Le serveur va attendre de se faire ping par un client pour emettre ou recevoir.
class Server:
    def __init__(self, socket):
        self.socket = socket

    def handle_request(self, data, client_address):
        if data == 's':
            receiver = Receiver(self.socket, client_address)
            self.socket.sendto(str.encode("ok"), client_address)
            receiver.receive()
        elif data == 'r':
            sender = Sender(self.socket, client_address)
            sender.send()

    def wait_for_client(self):
        self.socket.bind((SERVER_IP, SERVER_PORT))

        while True:
            packet, address = self.socket.recvfrom(1200)
            thread = threading.Thread(target = self.handle_request, args = (packet, address))
            thread.daemon = True
            thread.start()

class Sender:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address

    def send(self):
        lastPck = 0
        lastAckPck = 0
        fileSize = os.path.getsize(filePath)
        totalPck = math.ceil(fileSize / BUFFER_SIZE)  
        sentPcks = []

        with open("data.txt", "rb") as f:
            while True:
                while lastPck - lastAckPck < WINDOW_SIZE and lastPck < totalPck:
                    data = f.read(BUFFER_SIZE)

                    packet = Packet(lastPck, data, True if lastPck == totalPck - 1 else False)

                    # pickle permet de serialiser l'objet
                    self.socket.sendto(pickle.dumps(packet), self.address)
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

class Receiver:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address

    def receive(self):
        waitingFor = 0

        while True:
            packet, address = self.socket.recvfrom(1200)
            packet = pickle.loads(packet)

            if packet.seq == waitingFor:
                waitingFor += 1

                with open("server.txt", "a+b") as f:
                    f.write(packet.data)

                if packet.last:
                    break

            self.socket.sendto(str.encode(str(waitingFor)), address)

if sys.argv[1] == 's':
    server = Server(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    server.wait_for_client()
else:
    client = Client(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), (True if sys.argv[2] == 's' else False))
    client.file_transfer()