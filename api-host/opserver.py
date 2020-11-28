from opdash_api import OpDashAPI

api = OpDashAPI()

api.start(8080) # Non-blocking

while True:
    command = input(">>> ").lower().strip()
    if command in "exit quit close bye".split():
        api.stop()
    elif command == "get functions":
        for f in api.get_all_functions():
            print(f)
    elif command.split()[0] == "call":
        s = command.split()
        # ID is s[1]
        all_fs = api.get_all_functions()
        func = None
        for f in all_fs:
            if f["token"] == s[1]:
                func = f 
                break
        api.call_function(func, [10, "Jordan"])

    elif command == "get transactions":
        for t in api.transactions:
            print(api.transactions[t])