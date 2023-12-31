import os
import socket
import struct
import sys
import enum

class RequestType(enum.Enum):
    CREATE = 0x01
    READ = 0x02
    WRITE = 0x03
    REMOVE = 0X04
    FAIL = 0x05

class DFSServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"Server listening on {self.host}:{self.port}...")

        while True:
            conn, addr = self.socket.accept()
            print(f"Connection established from {addr}")
            self.handle_connection(conn)
    
    def handle_create_request(self, filename):
        file = open(filename, 'w')
        file.close()
        fh = os.path.abspath(filename)
        response = struct.pack("!BI", 0x01, len(fh)) + fh.encode()
        return response

    def handle_read_request(self, fh, offset, count):
        with open(fh, 'r') as f:
            f.seek(offset)
            data = f.read(count)
        return struct.pack("!BI", 0x02, len(data)) + data.encode()
    
    def handle_write_request(self, fh, offset, data):
        with open(fh, 'r+') as f:
            f.seek(offset)
            f.write(data)
        return struct.pack("!BI", 0x03, 0)
    
    def handle_remove_request(self, filename):
        os.remove(filename)
        return struct.pack("!BI", 0x04, 0)

    def handle_connection(self, conn):
        data = conn.recv(1024)
        print(f"Received data: {data}")
        if not len(data):
            conn.close()
            return
        match data[0]:
            case RequestType.CREATE.value:  # CREATE request
            # Extract filename from request
                filename_len = data[1]
                filename = data[2:2+filename_len].decode()

                # Create file and send file handle back to client
                response = self.handle_create_request(filename)
                conn.sendall(response)
            case RequestType.READ.value:  # READ request
                # Extract file handle, offset, and count from request
                fh_len = data[1]
                fh = data[2:2+fh_len].decode()
                offset = struct.unpack("!Q", data[2+fh_len:2+fh_len+8])[0]
                count = struct.unpack("!I", data[2+fh_len+8:2+fh_len+8+4])[0]

                # Read specified portion of file and send data back to client
                response = self.handle_read_request(fh, offset, count)
                conn.sendall(response)
            case RequestType.WRITE.value:  # WRITE request
                # Extract file handle, offset, and data from request
                fh_len = data[1]
                fh = data[2:2+fh_len].decode('utf-8')
                print(fh)
                offset = struct.unpack("!Q", data[2+fh_len:2+fh_len+8])[0]
                data_len = data[2+fh_len+8]
                data = data[2+fh_len+9:2+fh_len+9+data_len].decode()

                # Write data to file and send status code back to client
                response = self.handle_write_request(fh, offset, data)
                conn.sendall(response)
            case RequestType.REMOVE.value:  # REMOVE request
                # Extract filename from request
                filename_len = data[1]
                filename = data[2:2+filename_len].decode()

                # Remove file and send status code back to client
                response = self.handle_remove_request(filename)
                conn.sendall(response)

        conn.close()

if __name__ == "__main__":
    host = '0.0.0.0' # listen on all available interfaces
    port = int(sys.argv[1])
    server = DFSServer(host, port)
    server.start()