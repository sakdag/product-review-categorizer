import pandas as pd


def read_dataset(path):
    df = pd.read_csv(path)
    df_size = len(df)
    print('Data Size: ' + str(df_size))
    return df
