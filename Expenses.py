import datetime
import pandas as pd


class Expense:
    """def __init__(self, date: datetime, description: str, category: str, amount: float):
        self.date = date
        self.description = description
        self.category = category
        self.amount = amount"""

    def __init__(self):
        self.path = None

    def check_funds(self):
        pass

    def deposit(self):
        pass

    def import_expense_csv(self, path):
        """
        Read csv file in to Padans Dataframe
        :param path: path to csv file.
        :return: dataframe
        """
        self.path = path
        return pd.read_csv(path)

    def format_date(self, date):
        """
        Edit date format in pandas Dataframe from MM/DD/YYYY to DD/MM/YYYY
        :param date: Pandas series object
        :return: DD/MM/YYYY date string
        """




    def add_expense(self, date, description, category, amount):
        pass


class Income:
    def __init__(self, date: datetime, amount: float, source="", description=""):
        self.date = date
        self.amount = amount
        self.source = source

    pass
