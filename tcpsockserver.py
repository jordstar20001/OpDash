"""
TCP Socket Server wrapper / framework.
"""

import socket
import threading
import json
import traceback
import sys
import time

class UDPServer():
    def __init__(self, port, recv_callback, local = False, message_size = 4096, timeout = 2): # 2s timeout
        self.STARTTIME = time.time()
        self.recv_callback = recv_callback
        self.packet_bytes = message_size
        self.LOCAL = local
        self.LISTENING = False
        self.SOCKET = None
        self.address = (("0.0.0.0", "localhost")[local], port)
        self.TIMEOUT = timeout        

    def listen(self):
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(self.address)
        self.LISTENING = True

        self.__socket_recv_thread = threading.Thread(target=self.__SOCKET_RECV)
        self.__socket_recv_thread.daemon = True
        self.__socket_recv_thread.start()

        return self.__socket_recv_thread
        
    def send_object(self, data, addr):
        assert type(data) == dict, "Data must be a dictionary."
        data = json.dumps(data)

        self.SOCKET.sendto(data.encode("utf-8"), addr)

    def stop(self):
        self.LISTENING = False

    def __SOCKET_RECV(self):
        #print()
        #log("Socket just started receiving.")
        self.SOCKET.settimeout(self.TIMEOUT)
        while self.LISTENING:
            try:
                data, address = self.SOCKET.recvfrom(self.packet_bytes)
            except:
                continue
            try:
                data_json = json.loads(data.decode('utf-8'))
            except Exception as e:
                print(f"Invalid message '{data.decode('utf-8')}' - the data was unable to be parsed to JSON:\n >>> {e}")
                continue

            try:
                self.recv_callback(address, data_json)

            except Exception as e:
                print(type(e))
                log(f"Receive handle error: {e}")

        log("Server stopped listening.")

    def __str__(self):
        return f"{type(self)} | Listening: {self.LISTENING} | Address: {self.address[0]}:{self.address[1]}>"