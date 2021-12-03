import requests as req

get_locations = True # Faster if disabled

ip, port = input("Input IP (leave blank for localhost)\n>>> "), input("Input port (leave blank for port 80)\n>>> ")

if not ip: ip = "localhost"
if not port: port = 80

port = int(port)

address = f"http://{ip}:{port}"

endpoint = lambda route: f"{address}/{route}"

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

while True: # Outer loop, responsible for viewing all options
    # Get all info
    clients_available = req.get(endpoint("status")).json()
    lines = []
    for i,c in enumerate(clients_available):
        cinfo = c["info"]

        # Get GEOlocation using ipapi
        if not get_locations:
            geostr = "UNKNOWN"

        else:
            if cinfo['ip'] in ["localhost", "127.0.0.1"]:
                geoloc = req.get(f"http://ip-api.com/json").json()
                geostr = f"LOCAL COMPUTER ({geoloc['city']}, {geoloc['regionName']}, {geoloc['country']})"
            else:
                geoloc = req.get(f"http://ip-api.com/json/{cinfo['ip']}").json()
                geostr = f"{geoloc['city']}, {geoloc['regionName']}, {geoloc['country']}"

        lines.append(f"#{i+1} -> <{c['ID']}> [{cinfo['name']} running {cinfo['os']}] (IP: {cinfo['ip']} | Location: {geostr})")

    for l in lines: print(l)

    should_continue = False

    while True:
        try:
            selection = int(input("Select by #, or type 0 to refresh clients list\n>>> ")) - 1
            if selection == -1:
                break
            client_selected = clients_available[selection]
            should_continue = True
            break
        except KeyboardInterrupt:
            quit()
        except:
            print(f"Invalid input; make sure the number is 0 (refresh) OR between 1 and {len(clients_available)}.")
    
    if should_continue:
        # Get client specific info
        specifics = req.get(endpoint(f"status/{client_selected['ID']}")).json()
        subbed = specifics['info']['subscribed']
        print(f"[FUNCTIONS for client <{client_selected['ID']}> ({client_selected['info']['name']})")
        for i, s in enumerate(subbed):
            print("="*15)
            print(f"<{s['token']}>")
            print(f"#{i+1}: {s['title']}")
            if s["description"]: print(s['description'])
            print(f"\n(ARGS)")
            for a in s["args"]:
                print(f"{a[0]} of type {a[1]}")
            print("="*15)
        
        selection = int(input("Select a function to run it.")) - 1
        f_selected = subbed[selection]

        data_to_send = {}

        for a in f_selected["args"]:
            val = input(f"Input value for '{a[0]}' ({a[1]}): ")
            data_to_send[a[0]] = str_to_type[a[1]](val)

        resp = req.post(endpoint(f"run/{f_selected['token']}"), json=data_to_send)
        print(f"Transaction ID: {resp.text}")