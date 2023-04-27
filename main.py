# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import numpy as np

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hello, {name}')  # Press ⌘F8 to toggle the breakpoint.


def load_file():
    with open('Expenses.csv', 'r') as file:
        df = pd.DataFrame(data=file)




# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    print_hi('PyCharm')

    load_file()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
