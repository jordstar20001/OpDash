"""
OpDash API

Allows for the subscription of functions to be exposed to the web.
"""

from flask import Flask, jsonify, make_response, request

import os

from ezsocket_server import EZSServer, random_hex, timeit

from datetime import datetime as dt

from threading import Thread

from hashlib import sha256

from json import dumps, loads

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

class OpDashServer():
    def __init__(self):
        self.connections = {}
        self.transactions = {}
        self.webserver_thread = None

        self.functions_by_signature = {}

        self.f_info = {
            "secrets": "secrets",
            "creds": "creds.json",
            "salt": "salt.key"
        }

        self.ensure_creds()

    def load_salt(self):
        path = os.path.join(self.f_info["secrets"], self.f_info["salt"])
        if os.path.exists(path):
            return open(path, "rb").read()
        else:
            new_salt = random_hex(16).encode()
            open(path, "x")
            with open(path, "wb") as f: f.write(new_salt)
            return new_salt

    def ensure_creds(self):
        path = os.path.join(self.f_info["secrets"], os.path.join(self.f_info["creds"]))
        if not os.path.exists(path):
            open(path, "x")
            open(path, "w").write("{}")

    def login_with_creds(self, username, password):
        path = os.path.join(self.f_info["secrets"], self.f_info["creds"])
        password_hash = self.hash_password(password)
        current_users = loads(open(path, "r").read())
        if not current_users[username]:
            return False, "Username not found"
        else:
            if current_users[username] == password_hash:
                return True, "Success"
            else:
                return False, "Incorrect password"


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
            for sub in data["subscribed"]:
                if sub['signature'] not in self.functions_by_signature:
                    self.functions_by_signature[sub['signature']] = [(client.id, sub['token'])]
                else:
                    self.functions_by_signature[sub['signature']].append((client.id, sub['token']))
            data["sys_info"]["ip"] = client.address[0]
            self.connections[client.id]["info"] = data
        else:
            raise OpDashException(f"Invalid client with ID '{client.id}'")
    
    def get_client(self, cID):
        return self.connections[cID]

    def get_all_clients(self):
        res = []
        for cID in self.connections:
            c = {
                "ID": cID,
                "info": self.connections[cID]["info"]["sys_info"]
            }
            res.append(c)
        return res

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

    def hash_password(self, password):
        salt = self.load_salt()
        return sha256(password.encode() + salt).hexdigest()

    def create_user(self, username, password):
        path = os.path.join(self.f_info["secrets"], self.f_info["creds"])
        try:
            password_hash = self.hash_password(password)
            current_users = loads(open(path, "r").read())
        except Exception as e:
            return False, f"Failed to load data: {e}"
        if username in current_users:
            return False, "User already exists"

        else:
            current_users[username] = password_hash
            new_file_contents = dumps(current_users)
            with open(path, "w") as f:
                 f.write(new_file_contents)
            return True, "Success"

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
                "ID": ID,
                "info": self.connections[ID]["info"]
            }

            res.append(obj)

        return res

    def expose(self, port, blocking = False):
        app = Flask(__name__)

        @app.route("/status", methods=['GET'])
        def status():
            # get all of the connected clients
            return jsonify(self.get_all_clients())

        @app.route("/status/<id_search>", methods=['GET'])
        def status_by_id(id_search):
            conns = self.get_serialised_connections()
            for c in conns:
                if c["ID"] == id_search:
                    return jsonify(c)
            return 404, "Not found."

        @app.route("/run/<f_ID>", methods=["POST"])
        def run_function(f_ID):
            func_dict = {}
            try:
                func_dict = self.get_function_by_token(f_ID)

            except:
                return 404, "Not found."

            # Validate arguments
            args = request.json
            for a in func_dict["args"]:
                if not (a[0] in args and str_to_type[a[1]] == type(args[a[0]])):
                    return 400

            arg_lst = [args[k] for k in args]
            trans_token = self.call_function(func_dict, arg_lst)

            return trans_token

        @app.route("/transaction/<trans_ID>")
        def get_transaction(trans_ID):
            return jsonify(self.transactions[trans_ID])

        if blocking:
            app.run("0.0.0.0", port)
        else:
            t = Thread(target = app.run, args=("0.0.0.0", port))
            t.daemon = True
            t.start()