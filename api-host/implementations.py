import os
import math
from time import sleep
def run_command(cmd: str):
    """
    Run task 'task' and return the product of a and b
    """
    os.system(cmd)

def open_website(website: str):
    """
    Open site 'website' and return the sum of a and b
    """
    os.system(f"start chrome {website}")

def count_and_log(number: int):
    """
    Count to number "number", and return the natural log of the number.
    """
    for i in range(number):
        print(i + 1)
        sleep(1)

    return math.log(number)

from opdash import OpDashManager as mgr

def main():
    m = mgr()

    m.subscribe(run_command, "Function 1 - Command", "Run task 'task'.")

    m.subscribe(open_website, "Open site 'website'.")
    
    m.subscribe(count_and_log, "Count and ln.")

    m.start("60.241.83.158", 8080)

    input()

main()