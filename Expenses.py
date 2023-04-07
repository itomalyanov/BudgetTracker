import datetime


class Expense:

    def __init__(self, date: datetime, description: str, category: str, amount: float):
        self.date = date
        self.description = description
        self.category = category
        self.amount = amount

    def check_funds(self):
        pass

    def deposit(self):
        pass

    pass


class Income:
    def __init__(self, date: datetime, amount: float, source="", description=""):
        self.date = date
        self.amount = amount
        self.source = source

    pass
