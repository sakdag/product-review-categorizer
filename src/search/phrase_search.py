import os.path
import re
import string
from sys import argv

import pandas as pd
from nltk import word_tokenize, WordNetLemmatizer
from spellchecker import SpellChecker
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


def search_for(inverted_index, qp, query_phrases: list, result_limit: int = 10):

    query_as_string = ''
    for phrase in query_phrases:
        query_as_string = query_as_string + '"' + phrase + '"'

    q = qp.parse(query_as_string)

    return inverted_index.searcher().search(q, limit=result_limit)


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
def highlight_search_terms(results, query_phrases: list, lemmatizer, punctuation_regex, spell):
    modified_search_results = []

    for current_result in results:
        review_text = current_result['review']
        processed_result_tokens = []
        token_indices = []

        # Iterate over tokens to find where to highlight
        for token_index, token in enumerate(word_tokenize(review_text)):
            token = token.lower()

            # Fast version, misses misspelled highlights
            if token not in string.punctuation:

                # Lemmatize the token
                token = lemmatizer.lemmatize(token)

                processed_result_tokens.append(token)
                token_indices.append(token_index)

            # # Slow version, finds all highlights
            # # Is token combination of symbols only
            # if punctuation_regex.match(token) is None:
            #
            #     # Correct if token is misspelled
            #     misspelled = spell.unknown([token])
            #     if len(misspelled) > 0:
            #         token = spell.correction(list(misspelled)[0])
            #
            #     # Lemmatize the token
            #     token = lemmatizer.lemmatize(token)
            #
            #     processed_result_tokens.append(token)
            #     token_indices.append(token_index)

        highlight_indices = []
        num_of_tokens = len(processed_result_tokens)

        # For every token in processed tokens, check if phrase matches, if so,
        # calculate where to highlight in raw review.
        for i in range(num_of_tokens):
            for query_phrase in query_phrases:

                # Check for both original query phrase, and the one where tokens in
                # query phrase is swapped.
                matches_original_phrase = query_phrase.startswith(processed_result_tokens[i]) \
                    and i < num_of_tokens - 1 \
                    and query_phrase.endswith(processed_result_tokens[i + 1])

                query_phrase_tokens = query_phrase.split(' ')
                swapped_query_phrase = query_phrase_tokens[1] + ' ' + query_phrase_tokens[0]
                matches_swapped_phrase = swapped_query_phrase.startswith(processed_result_tokens[i]) \
                    and i < num_of_tokens - 1 \
                    and swapped_query_phrase.endswith(processed_result_tokens[i + 1])

                if matches_original_phrase or matches_swapped_phrase:
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
    punctuation_regex = re.compile(r'(([^\w\s])+)')
    spell = SpellChecker()

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
        qp = QueryParser("lemmatizedReview", schema=ix.schema)

        phrases_to_query = ['sound quality', 'volume control']
        results = search_for(ix, qp, phrases_to_query)

        lemmatizer = WordNetLemmatizer()
        search_results = highlight_search_terms(results, phrases_to_query, lemmatizer,
                                                punctuation_regex, spell)

        for result in search_results:
            print(result)
