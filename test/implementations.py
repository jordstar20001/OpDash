import os

def do_some_stuff(task: str, a: int, b: int):
    """
    Run task 'task' and return the product of a and b
    """
    os.system(f"start {task}")
    return a * b

def do_some_other_stuff(website: str, a: int, b: int):
    """
    Open site 'website' and return the sum of a and b
    """
    os.system(f"start chrome {website}")
    return a + b

from opdash import OpDashManager as mgr

m = mgr()

m.subscribe(do_some_stuff, "Function 1 - Product", "Run task 'task' and return the product of a and b")

m.subscribe(do_some_stuff, "Open site 'website' and return the sum of a and b")

m.start("localhost", 8080)

input()