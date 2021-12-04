from opdash_server import OpDashServer
from time import sleep
api = OpDashServer()
from getpass import getpass
api.start(8080) # Non-blocking

api.expose(80, blocking = False) # Blocking, and should only be exposed if nothing else is happening.

while True:
    try:
        command = input(">>> ").lower().strip()
        if command in "exit quit close bye".split():
            api.stop()
            quit()
        elif command == "get functions":
            for f in api.get_all_functions():
                print(f)
        elif command.split()[0] == "add_account":
            api.auth.create_user(input("username : "), getpass("password : "))
            print("User created!")
        elif command.split()[0] == "call":
            s = command.split()
            all_fs = api.get_all_functions()
            func = None
            for f in all_fs:
                if f["token"] == s[1]:
                    func = f 
                    break
            api.call_function(func, [10, "Jordan"])

        elif command == "add user":
            u, p = input("user: "), input("pass: ")
            print(api.create_user(u, p))

        elif command == "d":
            print(api.get_serialised_connections())

        elif command == "e":
            print(api.get_all_functions())
        elif command == "f":
            print(api.connections)
        elif command == "get transactions":
            for t in api.transactions:
                print(api.transactions[t])
    except KeyboardInterrupt:
        api.stop()
        quit()