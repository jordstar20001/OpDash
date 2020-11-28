"""
OpDash host library

Allows for the subscription of functions to be exposed to the web.
"""

from ezsocket_client import EZSClient

import inspect, binascii, os
from datetime import datetime as dt
import platform as pltfm
from inspect import signature as sig

import threading as thd

from copy import copy, deepcopy

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

class ExecReturn():
    def get(self):
        return self.obj

    def set(self, v):
        self.obj = v

    def __str__(self):
        return str(self.obj)

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

    def get_system_info():
        return {
            "os": f"{pltfm.system()} {pltfm.release()} v{pltfm.version()}",
            "time": f"{dt.now().hour}:{dt.now().minute}:{dt.now().second} - {dt.now().day}/{dt.now().month}/{dt.now().year}",
            "name": pltfm.node()
        }


    def __init__(self):
        self.subscribed_callables = {
            "sys_info": OpDashManager.get_system_info(),
            "subscribed": {}

        }

        self.connected = False

    def start(self, ip, port, listen_daemon = False):
        self.socket_client = EZSClient()

        self.socket_client.connect(ip, port)

        self.connected = True

        self.socket_client.on("request publish", self.on_request_publish)

        self.socket_client.on("call request", self.on_call_request)

        if self.subscribed_callables["subscribed"] != {}:
            self.publish()

    def stop(self):
        self.socket_client.shutdown()

    def on_request_publish(self, client, data = None):
        self.publish()

    def on_call_request(self, data):
        token = data["token"]
        self.call_by_id(token, data["args"], data["transaction"])

    def publish(self):
        """
        Publish subscribed functions to the API.
        """
        if self.connected:
            res = deepcopy(self.subscribed_callables)
            subbed = []
            for token in res["subscribed"]:
                subbed.append(res["subscribed"][token][1])
            res["subscribed"] = subbed
            self.socket_client.send("publish", res)
        
    def subscribe(self, c, title, desc = "", arg_types = None):
        info = OpDashManager.create_callable_info(c, title, desc, arg_types)
        self.subscribed_callables["subscribed"][info["token"]] = [c, info]
        self.publish()
        return info["token"]
    
    def unsubscribe(self, token):
        del self.subscribed_callables["subscribed"][token]
        self.publish()
    
    def sub_decor(self, function):
        self.subscribe(function, )

    def call_by_id(self, token, args, transactionID):
        # Check if args matches
        required_number = len(sig(self.subscribed_callables["subscribed"][token][0]).parameters.values())
        if len(args) != required_number:
            raise ValueError(f"Didn't provide {required_number} ARGS")
        
        # TODO ensure args are in correct order
        args = [args[k] for k in args]
        
        func = self.subscribed_callables["subscribed"][token][0]

        return_obj = ExecReturn()

        func_thread = thd.Thread(target=self.__T_function_exec, daemon=True, args=(func, args, transactionID))

        func_thread.start()

    def __T_function_exec(self, c, args, tID):
        return_value = c(*args)
        self.function_finish(return_value, tID)
        
    def function_finish(self, ret, tID):
        self.socket_client.send("function return", {
            "transaction": tID,
            "result": ret
        })