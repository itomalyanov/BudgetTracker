import datetime
import pandas as pd
class Income:

    def __init__(self, date: datetime, source: str, amount: float):
        self.date = date
        self.source = source
        self.amount = amount


    def import_from_file(self, path):
        pass
