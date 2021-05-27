import os.path

import pandas as pd
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh import index
from whoosh.qparser import QueryParser

import src.util.categorizer_utils as cu
from src.config.config import Config


def add_documents_to_index(df: pd.DataFrame, ix):
    writer = ix.writer()

    for df_index, row in df.iterrows():
        writer.add_document(review=row['reviewText'], productId=row['asin'])

    writer.commit()


def search_for(ix, query: str):
    qp = QueryParser("review", schema=ix.schema)
    q = qp.parse(query)

    with ix.searcher() as searcher:
        results = searcher.search(q)

        for result in results:
            print(result)


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    preprocessed_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

    df = cu.read_dataset(preprocessed_file_name)

    # Create schema
    schema = Schema(review=TEXT(stored=True), productId=TEXT(stored=True))

    # Create index
    dirname = os.path.dirname(__file__)
    index_dir = os.path.join(dirname, Config.INDEX_PATH)

    ix = index.create_in(index_dir, schema=schema)

    add_documents_to_index(df, ix)

    search_for(ix, 'sound quality')
