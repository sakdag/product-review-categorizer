import json

import pandas as pd


def read_dataset(path):
    df = pd.read_csv(path)
    df_size = len(df)
    print('Data Size: ' + str(df_size))
    return df


def read_popular_phrases(path):
    phrases_file = open(path, 'r')
    lines = phrases_file.readlines()
    phrases_file.close()

    phrase_dict = {'phrases': []}
    for line in lines:
        phrase_dict['phrases'].append(line.split(':')[0])

    return json.dumps(phrase_dict)
