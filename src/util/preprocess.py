import json
import sys
import pandas as pd

sys.path.append("..")

from config.config import Config


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
            i += 1
            obj = json.loads(line)
            if obj['asin'] in product_id_list:
                data.append(obj)
            if i == 500000:
                break
    return data


if __name__ == '__main__':
    # Read metadata
    metadata = read_data(Config.ELECTRONICS_METADATA_PATH)
    print('Total:', len(metadata))

    # Filter items with categories containing 'headphone' keyword
    headphones_metadata = [item for item in metadata if len([c for c in item['category'] if 'headphone' in c.lower()]) > 0]
    print('Headphones:', len(headphones_metadata))

    write_data(Config.HEADPHONES_METADATA_PATH, headphones_metadata)

    headphones_df = pd.read_json(Config.HEADPHONES_METADATA_PATH)
    product_id_list = list(headphones_df['asin'].values)

    # Read and filter reviews
    headphones_reviews = read_filter_data(Config.ELECTRONICS_REVIEWS_PATH, product_id_list)
    print('Total:', len(headphones_reviews))

    write_data(Config.HEADPHONES_REVIEWS_PATH, headphones_reviews)

