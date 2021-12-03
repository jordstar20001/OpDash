from opdash import OpDashManager as mgr

m = mgr()

def func(number: int, name: str):
    print(f"Name: {name} and number: {number}")
    return {
        "info": [1,2,3,4,5],
        "more_stuff": "hello!"
    }

m.subscribe(func, "This is a title.")

m.start("localhost", 8080)

while True:
    command = input(">>> ").lower().strip()
    if command in "exit quit close bye".split():
        m.stop()
        break