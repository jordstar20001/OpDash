"""
EZ Socket Client for Python

Jordan Zdimirovic - https://github.com/jordstar20001/ez-sockets.git
"""

import socket, json, threading

from typing import Dict, Callable

DEBUG = False # TRUE to enable debug console messages

#region Helper Functions
def get_event_and_content(data):
    event_end = data.find("\n")
    event, content = data[:event_end], data[event_end + 1:].strip()
    if content.strip() != "": content = json.loads(content)
    else: content = None
    return (event, content)
#endregion

class EZSClient():
    """
    EZ-Socket Client Class.
    Handles incoming socket connections, events and sending / receiving.

    First, create an instance.
    Then, call the connect method. Provide the server address / port, as well as an optional disconnect callback
    """
    def __T_get_incoming(self):
        """
        Thread that handles incoming messages from the server.
        Handles disconnects.
        """
        while self.listening:
            try:
                data = self.TCPSOCKET.recv(self.msg_size)
                if data == b'':
                    # The socket has been disconnected.
                    self.shutdown()
                    return
                try:
                    data = data.decode()
                    event, content = get_event_and_content(data)
                    self.__handle_event(event, content)

                except Exception as e:
                    if DEBUG: print(f"Format of data was incorrect and subsequently caused an error:\n{e}")

            except Exception as e:
                if DEBUG: print(f"Error when receiving data:\n{e}")
                self.shutdown()
                return


    def __init__(self):
        self.TCPSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.event_registry = {} # event key -> callable
        self.disconnect_callback = None

    def shutdown(self):
        """
        Stop the client.
        This just means to stop listening, and call the disconnect callback (for now)
        """
        self.listening = False
        if self.disconnect_callback: self.disconnect_callback()
        # Do anything else that is necessary

    def connect(self, ip: str, port: int, msg_size: int = 1024, disconnect_callback: Callable = None):
        """
        Connect to an EZSServer instance.
        Calls the listen thread and connects the two sockets.
        """
        self.listening = True
        self.msg_size = msg_size
        self.server_address = (ip, port)
        self.TCPSOCKET.connect(self.server_address)
        self.disconnect_callback = disconnect_callback
        t = threading.Thread(target=self.__T_get_incoming, daemon=True)
        t.start()

    def on(self, event: str, callback: Callable):
        """
        Register an event with a callback.
        """
        self.event_registry[event] = callback
    
    def __handle_event(self, event: str, data: Dict = None):
        """
        Handle the event with the data given.
        """
        if event in self.event_registry:
            self.event_registry[event](data)

    def send(self, key: str, data: Dict = None):
        """
        Send a message to the server.
        """
        packet = key + '\n'
        packet += json.dumps(data)
        self.TCPSOCKET.send(packet.encode())