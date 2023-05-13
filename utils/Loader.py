import pandas as pd


def load_file(path):
    with open(path, 'r') as file:
        df = pd.DataFrame(data=file)


def filter_active(df):
    df = df[df['Complete'] == True]
    return df


def filter_currency_amount():
    df['Debits']