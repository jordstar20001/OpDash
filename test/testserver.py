from ezsocket_server import EZSServer

server = EZSServer()

server.listen(8081)

def on_connect(c, d):
    print(f"Connected: {c.id}")
def on_disconnect(c, d):
    print(f"Disconnected: {c.id}")
    
server.on("connect", on_connect)
server.on("disconnect", on_disconnect)

input()