"""
EZ Socket Server for Python

Jordan Zdimirovic - https://github.com/jordstar20001/ez-sockets.git
"""

import time, sys, os, json, threading, socket, binascii, timeit

from typing import Dict, Callable

DEBUG = False # TRUE to enable debug console messages

#region Helper Functions
def random_hex(length: int):
    return binascii.b2a_hex(os.urandom(length // 2)).decode()
def dict2tup(d):
    return [(k, d[k]) for k in d.keys()]
def secs2timestr(seconds):
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    number_word_pairs = [(hours, "hrs"), (minutes, "mins"), (seconds, "secs")]
    return ", ".join([f"{number} {word}" for number, word in number_word_pairs])
def get_event_and_content(data):
    event_end = data.find("\n")
    event, content = data[:event_end], data[event_end + 1:].strip()
    if content.strip() != "": content = json.loads(content)
    else: content = None
    return (event, content)
#endregion

class EZSConnectedClient():
    """
    EZ-Socket Client Connection Class.
    Represents a remote client. Allows for an object-representation of our clients.

    These instances are created automatically by the EZSServer instance,
    and hence should not be created manually.
    """
    def __init__(self, server, ident: str, sock, address: tuple):
        self.sock = sock
        assert type(sock) == socket.socket, "Argument 'socket' must be a valid socket."
        self.id = ident
        self.address = address
        self.server = server
        self.connected = True
        self.connect_time = int(timeit.default_timer())

    def send(self, key: str, data: Dict = None):
        """
        Send a message to this client.
        """
        packet = key + '\n'
        if data:
            packet += json.dumps(data)
        try:
            self.sock.send(packet.encode())
        except ConnectionResetError:
            # Failed to send, disconnect the client now.
            self.server.disconnect_client(self.id)

    def disconnect(self):
        """
        Shutdown and close this client socket.
        """
        self.sock.shutdown(socket.SHUT_RDWR) # Shutdown the socket, don't allow any sends nor receives
        self.sock.close()
        self.connected = False

    def age(self):
        """
        Returns the age in seconds of this client.
        """
        return timeit.default_timer() - self.connect_time

    def __str__(self):
        return f"Client: {self.id}, connected {secs2timestr(int(self.age()))} ago."

class EZSServer():
    def __init__(self):
        self.listening = False
        
        self.__threads = {}

        self.__connected_clients = {}

        self.event_registry = {}

    def __T_get_incoming(self) -> None:
        """
        Thread that handles incoming socket connections.
        Is started by the listen() method.
        """
        while self.listening:
            sock, addr = self.TCPSOCKET.accept()
            token = random_hex(16)
            if DEBUG: print(f"Socket '{token}' at {addr[0]} connected.")
            client = EZSConnectedClient(self, token, sock, addr)
            self.__connected_clients[token] = client
            self.__call_event(client, "connect", None)
            self.__threads[token] = threading.Thread(target=self.__T_client, args=(client,))
            self.__threads[token].start()
    
    def on(self, event: str, callback: Callable):
        """
        Register a callback to an event.
        """
        # TODO assert function signature
        self.event_registry[event] = callback
    
    def __call_event(self, client: EZSConnectedClient, event: str, data: Dict):
        """
        Call the event callback method if it exists.
        """
        if event in self.event_registry:
            self.event_registry[event](client, data)
    
    def get_clients(self) -> tuple:
        """
        Get clients as key-value tuples
        eg: [(ID, client), (ID, client), ...]
        """
        return dict2tup(self.__connected_clients)

    def disconnect_client(self, ident: str):
        """
        Disconnect the client given by the ID 'ident'.
        """
        # Call the disconnect callback (if it exists)
        self.__call_event(self.__connected_clients[ident], "disconnect", None)
        self.__connected_clients[ident].disconnect()
        del self.__connected_clients[ident]

    def disconnect_all(self):
        """
        Disconnect all clients currently connected to the server.
        """
        for c, _ in self.get_clients():
            self.disconnect_client(c)

    def __T_client(self, client: EZSConnectedClient):
        """
        Client socket thread. This thread runs while the client is connected,
        and handles all new messages from this client.

        If at any point the client becomes disconnected, this thread will
        handle the proper disconnection of the socket.
        """
        while client.connected:
            try:
                data = client.sock.recv(self.msg_size)
                data = data.decode()
                
                try:
                    event, content = get_event_and_content(data)
                except:
                    if DEBUG:
                        print("Data sent was in the incorrect format. Parsing to JSON failed.")

                self.__call_event(client, event, content)
            except:
                if DEBUG: print(f"Client {client.id} lost connection.")
                if client.connected:
                    self.disconnect_client(client.id)

    def listen(self, port: int, local: bool = False, msg_size = 1024, recv_timeout = 1, max_connections = 50) -> None:
        """
        Begin listening for new connections.
        Setup is done in this function - the socket is created, bound and started.
        """
        self.listening = True

        self.TCPSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV4, TCP

        self.msg_size = msg_size

        self.address = (socket.gethostname(), "localhost")[local]

        self.port = port

        self.TCPSOCKET.bind((self.address, self.port))

        self.TCPSOCKET.listen(max_connections)

        self.__threads = {
            "listening": threading.Thread(target=self.__T_get_incoming, daemon=True)
        }
        
        for t in self.__threads:
            self.__threads[t].start()

    def broadcast(self, event: str, data: Dict) -> None:
        """
        Sends the specified message to all connected clients.
        """
        for _, c in self.get_clients():
            c.send(event, data)