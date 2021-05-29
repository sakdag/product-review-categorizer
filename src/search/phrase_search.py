import os.path
from sys import argv

import pandas as pd
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh import index
from whoosh.qparser import QueryParser

import src.util.categorizer_utils as cu
from src.config.config import Config


def add_documents_to_index(df: pd.DataFrame, ix):
    writer = ix.writer()

    for df_index, row in df.iterrows():
        writer.add_document(review=row['reviewText'],
                            reviewChunks=row['preprocessedReviewChunks'],
                            productId=row['asin'])

    writer.commit()


def search_for(inverted_index, query_phrases: list):
    qp = QueryParser("reviewChunks", schema=inverted_index.schema)

    query_as_string = ''
    for phrase in query_phrases:
        query_as_string = query_as_string + '"' + phrase + '"'

    q = qp.parse(query_as_string)

    with ix.searcher() as searcher:
        return searcher.search(q)


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    index_dir = os.path.join(dirname, Config.INDEX_PATH)

    if len(argv) == 2 and argv[1] == 'createIndex':
        preprocessed_file_name = os.path.join(dirname, Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

        df = cu.read_dataset(preprocessed_file_name)

        # Create schema
        schema = Schema(review=TEXT(stored=True),
                        productId=TEXT(stored=True),
                        reviewChunks=TEXT(stored=True))

        # Create index
        ix = index.create_in(index_dir, schema=schema)
        add_documents_to_index(df, ix)

    else:
        ix = index.open_dir(index_dir)

        phrases_to_query = ['sound quality', 'volume control']
        results = search_for(ix, phrases_to_query)

        for result in results:
            print(result)
