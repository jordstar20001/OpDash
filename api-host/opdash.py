"""
OpDash host library

Allows for the subscription of functions to be exposed to the web.
"""

from ezsocket_client import EZSClient

import inspect, binascii, os
from inspect import signature as sig

str_to_type = {
    "str": str,
    "int": int,
    "bool": bool
}

type_to_str = {
    str: 'str',
    int: 'int',
    bool: 'bool'
}

#region Helper Functions
def random_hex(length: int):
    return binascii.b2a_hex(os.urandom(length // 2)).decode()
#endregion

class OpDashManager():
    """
    Manages subscribed functions etc
    """
    def create_callable_info(c, title, description, arg_types: list = None):
        params = list(sig(c).parameters.values())
        
        if arg_types == None and all(p.annotation != inspect._empty for p in params):
            arg_types = [p.annotation for p in params]
        elif len(arg_types) != len(params):
            raise ValueError("Could not deduce types for parameters.")
            
        params_str = []
        for i, t in enumerate(arg_types):
            if t not in type_to_str:
                raise ValueError(f"Parameter '{str(params[i])}'s type, '{t}', is not supported.")
            params_str.append(type_to_str[t])

        args = [[params[i].name, params_str[i]] for i in range(len(params))]

        return {
            "token": random_hex(30),
            "title": title,
            "description": description,
            "args": args
        }


    def __init__(self, ip, port):
        self.subscribed_callables = {
            
        }

        self.socket_client = EZSClient()

        self.socket_client.connect(ip, port)

        self.socket_client.on("call request", on_call_request)

    def on_call_request(data):
        token = data["token"]
        self.call_by_id(token, data["args"])

    def publish():
        """
        Publish subscribed functions to the API.
        """
        self.socket_client.send("callables update", self.subscribed_callables)
        
    def subscribe(self, c, title, desc = "", arg_types = None):
        info = OpDashManager.create_callable_info(c, title, desc, arg_types)
        self.subscribed_callables[info["token"]] = (c, info)
    
    def call_by_id(self, token, args):
        # Check if args matches
        required_number = len(sig(self.subscribed_callables[token][0]).parameters.values())
        if len(args) != required_number:
            raise ValueError(f"Didn't provide {required_number} ARGS")

        args = [args[k] for k in args]

        self.subscribed_callables[token][0](*args)

    def persist(self):
        while self.socket_client.listening:
            pass
    