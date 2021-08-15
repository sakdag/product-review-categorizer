import json
import sys

import pandas as pd

from datetime import datetime

import src.config.config as conf

sys.path.append("..")


def read_data(filepath):
    data = []
    with open(filepath) as f:
        for line in f:
            data.append(json.loads(line))
    return data


def write_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f)


def read_filter_data(filepath, product_id_list):
    data = []
    i = 0
    with open(filepath) as f:
        for line in f:
            obj = json.loads(line)
            if obj['asin'] in product_id_list and obj['verified'] and 'reviewText' in obj and len(obj['reviewText']) > 50:
                i += 1
                data.append(obj)
                if i == 50000:
                    break
    return data


if __name__ == '__main__':
    # Read metadata
    metadata = read_data(conf.ELECTRONICS_METADATA_PATH)
    print('Total:', len(metadata))

    # Filter items with categories containing 'headphone' keyword
    headphones_metadata = [item for item in metadata if
                           len([c for c in item['category'] if 'headphone' in c.lower()]) > 0]
    print('Headphones:', len(headphones_metadata))

    write_data(conf.HEADPHONES_METADATA_PATH, headphones_metadata)

    headphones_df = pd.read_json(conf.HEADPHONES_METADATA_PATH)
    product_id_list = list(headphones_df['asin'].values)

    start = datetime.now()

    # Read and filter reviews
    headphones_reviews = read_filter_data(conf.ELECTRONICS_REVIEWS_PATH, product_id_list)
    print('Total:', len(headphones_reviews))
    print('Time:', (datetime.now() - start).total_seconds())

    write_data(conf.HEADPHONES_REVIEWS_PATH, headphones_reviews)

    headphones_df = pd.read_json(conf.HEADPHONES_REVIEWS_PATH)
    headphones_df = headphones_df[['asin', 'overall', 'vote', 'reviewTime',
                                   'reviewerID', 'reviewerName', 'summary', 'reviewText']]
    headphones_df.to_csv(conf.HEADPHONES_REVIEWS_CSV_PATH, index=False)
