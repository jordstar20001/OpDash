"""
OpDash API

Allows for the subscription of functions to be exposed to the web.
"""

from flask import Flask

from ezsocket_server import EZSServer, random_hex, timeit

from datetime import datetime as dt

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

def time_str():
    return f"{dt.now().hour}:{dt.now().minute}:{dt.now().second} - {dt.now().day}/{dt.now().month}/{dt.now().year}"

class OpDashException(Exception):
    pass

class OpDashAPI():
    def __init__(self):
        self.connections = {}
        self.transactions = {}
    
    def valid_client_ID(self, cID):
        return cID in self.connections

    def on_client_connect(self, client, data = None):
        self.connections[client.id] = {
            "info": {},
            "client": client
        }

        client.send("request publish", {})

    def on_client_disconnect(self, client, data = None):
        del self.connections[client.id]

    def on_publish(self, client, data):
        if self.valid_client_ID(client.id):
            self.connections[client.id]["info"] = data
        else:
            raise OpDashException(f"Invalid client with ID '{client.id}'")
    
    def get_client(self, cID):
        return self.connections[cID]

    def get_owner(self, fToken):
        for cID in self.connections:
            for sub in self.connections[cID]["info"]["subscribed"]:
                if sub["token"] == fToken:
                    return self.connections[cID]["client"]

        raise Exception(f"Token {fToken} not a valid function token")

    def get_function_by_token(self, fToken):
        for cID in self.connections:
            for sub in self.connections[cID]["info"]["subscribed"]:
                if sub["token"] == fToken:
                    return sub
        
        raise Exception(f"Token {fToken} not a valid function token")

    def get_client_function(self, cID, index):
        assert self.valid_client_ID(cID), f"Client ID {cID} not valid."
        assert index < len(self.connections[cID]["info"]["subscribed"]), f"Index {index} out of range."
        return self.connections[cID]["info"]["subscribed"][index]

    def get_all_functions(self):
        funcs = []
        for cID in self.connections:
            for sub in self.connections[cID]["info"]["subscribed"]:
                funcs.append(sub)
        
        return funcs

    def start(self, port):
        self.socket_server = EZSServer()
        self.socket_server.listen(port)
        self.socket_server.on("connect", self.on_client_connect)
        self.socket_server.on("disconnect", self.on_client_disconnect)
        self.socket_server.on("publish", self.on_publish)
        self.socket_server.on("function return", self.on_return_value)

    def stop(self):
        self.socket_server.stop()


    def on_return_value(self, client, data):
        #TODO Validate
        transaction, result = data["transaction"], data["result"]
        self.transactions[transaction]["completed"] = True
        self.transactions[transaction]["result"] = result
        self.transactions[transaction]["f_time_raw"] = timeit.default_timer()
        self.transactions[transaction]["f_time"] = time_str()
        self.transactions[transaction]["duration"] = self.transactions[transaction]["f_time_raw"] - self.transactions[transaction]["i_time_raw"]
        
    def call_function(self, funcDict, args) -> str:
        args_required = funcDict["args"]
        assert len(args) == len(args_required), "Args length mismatch."
        for i in range(len(args)):
            if type(args[i]) != str_to_type[args_required[i][1]]:
                raise ValueError(f"Arg at index {i} should be {args_required[i][1]}, not {type(args[i])}")
        
        transaction_token = random_hex(10)
        
        packet = {
            "token": funcDict["token"],
            "transaction": transaction_token,
            "args": {
                args_required[i][0]: args[i] for i in range(len(args))
            }
        }
        
        transaction = {
            "completed": False,
            "result": None,
            "fToken": packet["token"],
            "args": packet["args"],
            "i_time_raw": timeit.default_timer(),
            "i_time": time_str(),
            "f_time_raw": None,
            "f_time": None
        }

        self.transactions[transaction_token] = transaction

        self.get_owner(funcDict["token"]).send("call request", packet)
        
        return transaction_token

    def get_serialised_connections(self) -> dict:
        res = []
        for ID in self.connections:
            obj = {
                "id": ID,
                "info": self.connections[ID]["info"]
            }

            res.append(obj)

        return res