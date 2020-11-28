from opdash import OpDashManager as mgr

m = mgr()

def func(number: int, name: str):
    print(f"Name: {name} and number: {number}")
    return "That worked!"

m.subscribe(func, "This is a title.")

m.start("localhost", 8080)
while True:
    command = input(">>> ").lower().strip()
    if command in "exit quit close bye".split():
        m.stop()