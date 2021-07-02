import os.path
from sys import argv

import pandas as pd
from nltk import word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh import index
from whoosh.qparser import QueryParser

import src.util.categorizer_utils as cu
from src.config.config import Config
from src.entity.search_result import SearchResult


def add_documents_to_index(df: pd.DataFrame, ix):
    writer = ix.writer()

    for df_index, row in df.iterrows():
        writer.add_document(reviewId=row['reviewId'],
                            review=row['reviewText'],
                            lemmatizedReview=row['lemmatizedReview'],
                            productId=row['asin'])

    writer.commit()


def search_for(inverted_index, query_phrases: list):
    qp = QueryParser("lemmatizedReview", schema=inverted_index.schema)

    query_as_string = ''
    for phrase in query_phrases:
        query_as_string = query_as_string + '"' + phrase + '"'

    q = qp.parse(query_as_string)

    return inverted_index.searcher().search(q)


# Following method assumes that both tokens and query phrases are of 2 words in size
# Returns search results in following format: List of
# (Review Id,
# Review text,
# ProductId,
# Ranking score of result,
# (Highlight index, number of words to highlight),
# (Highlight index, number of words to highlight),
# .
# .
# (Highlight index, number of words to highlight))
def highlight_search_terms(results, query_phrases: list, stop, lemmatizer):
    modified_search_results = []
    for current_result in results:
        review_text = current_result['review']
        processed_result_tokens = []
        token_indices = []
        for token_index, token in enumerate(word_tokenize(review_text)):
            token = token.lower()
            if token not in stop:
                token = lemmatizer.lemmatize(token)
                processed_result_tokens.append(token)
                token_indices.append(token_index)
        highlight_indices = []
        num_of_tokens = len(processed_result_tokens)
        for i in range(num_of_tokens):
            for query_phrase in query_phrases:
                if query_phrase.startswith(processed_result_tokens[i]) \
                        and i < num_of_tokens - 1 \
                        and query_phrase.endswith(processed_result_tokens[i + 1]):
                    highlight_indices.append((token_indices[i], 2))
        modified_search_results.append(SearchResult(
            current_result['reviewId'],
            review_text,
            current_result['productId'],
            current_result.score,
            highlight_indices
        ))

    return modified_search_results


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    index_dir = os.path.join(dirname, Config.INDEX_PATH)

    if len(argv) == 2 and argv[1] == 'createIndex':
        preprocessed_file_name = os.path.join(dirname, Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

        df = cu.read_dataset(preprocessed_file_name)

        # Create schema
        schema = Schema(reviewId=NUMERIC(stored=True),
                        review=TEXT(stored=True),
                        productId=TEXT(stored=True),
                        lemmatizedReview=TEXT(stored=True))

        # Create index
        ix = index.create_in(index_dir, schema=schema)
        add_documents_to_index(df, ix)

    else:
        ix = index.open_dir(index_dir)

        phrases_to_query = ['sound quality', 'volume control']
        results = search_for(ix, phrases_to_query)

        stop = stopwords.words('english')
        lemmatizer = WordNetLemmatizer()
        search_results = highlight_search_terms(results, phrases_to_query, stop, lemmatizer)

        for result in search_results:
            print(result)
