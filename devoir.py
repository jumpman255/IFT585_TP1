import sys, socket

BUFFER_SIZE = 10

def main(args):
    ip = args[1]
    port = args[2]
    listen = args[3] == '-l'
    if not listen:
        file = args[3]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if listen:
        sock.bind((ip, int(port)))

        while(True):
            bytesAddressPair = sock.recvfrom(BUFFER_SIZE)

            message = bytesAddressPair[0]

            # address = bytesAddressPair[1]

            # clientMsg = "Message from Client:{}".format(message)
            # clientIP  = "Client IP Address:{}".format(address)

            with open('test.txt', 'a+b') as wfile:
                wfile.write(message)

    else:
        with open(file, 'rb') as fp:
            data = fp.read(BUFFER_SIZE)

            while data:
                sock.sendto(data, (ip, int(port)))
                data = fp.read(BUFFER_SIZE)

main(sys.argv)

# python devoir.py 127.0.0.1 9000 -l
# python devoir.py 127.0.0.1 9000 zizi.txt