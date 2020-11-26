from opdash import OpDashManager as mgr

def function(number: int, name: str):
    print(f"Name: {name} and number: {number}")

m = mgr("localhost", 8080)

m.subscribe(function, "Function", "A very epic method.")

print(m.subscribed_callables)

m.persist()