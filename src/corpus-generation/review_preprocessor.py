import os
import re
import string

import nltk as nltk
import numpy as np
import pandas as pd
from nltk import tokenize, RegexpParser, pos_tag, word_tokenize, Tree
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from spellchecker import SpellChecker

from src.config.config import Config
from src.util import categorizer_utils as cu

# Defining a grammar & Parser
NP = "NP: {(<VBD\w?>|<NNP\w?>|<NNPS\w?>|<NN\w?>)+.*(<VBG\w?>|<NNP\w?>|<NNPS\w?>|<NN\w?>)}"
chunker = RegexpParser(NP)


def preprocess_and_save(df: pd.DataFrame, lemmatizer, preprocessed_file_name: str):
    chunk_func = chunker.parse
    stop = stopwords.words('english')
    spell = SpellChecker()
    punctuation_regex = re.compile(r'(([^\w\s])+)')

    for index, row in df.iterrows():

        # Get lemmatized version of the review and save
        lemmatized_review = ''
        for token in word_tokenize(row['reviewText']):

            # Is token combination of symbols only
            if punctuation_regex.match(token) is None:

                # Correct if token is misspelled
                misspelled = spell.unknown([token])
                if len(misspelled) > 0:
                    token = spell.correction(list(misspelled)[0])

                # Lemmatize the token and add
                if lemmatized_review != '':
                    lemmatized_review += ' '
                lemmatized_review += lemmatizer.lemmatize(token)

            elif token in string.punctuation:
                lemmatized_review += token

        df.loc[index, 'lemmatizedReview'] = lemmatized_review

        # Generate review chunks and save
        sentences = tokenize.sent_tokenize(lemmatized_review)

        review_chunks_as_string = process_review(sentences, chunk_func, stop)
        df.loc[index, 'preprocessedReviewChunks'] = review_chunks_as_string

    # Save
    df.replace('', np.NaN, inplace=True)
    df.dropna(subset=['preprocessedReviewChunks'], inplace=True)
    df.to_csv(preprocessed_file_name, index_label='reviewId')


def process_review(sentences: list, chunk_func, stop):
    review_chunks_as_string = ''

    for sentence in sentences:
        chunked = chunk_func(pos_tag(word_tokenize(sentence)))
        review_chunks = []
        current_chunk = []

        for subtree in chunked:
            if type(subtree) == Tree:
                current_chunk.append(" ".join([token for token, pos in subtree.leaves()]))
            elif current_chunk:
                named_entity = " ".join(current_chunk)

                if named_entity not in review_chunks:
                    review_chunks_as_string = process_found_named_entity(named_entity, stop, review_chunks_as_string)
                    current_chunk = []
            else:
                continue

    return review_chunks_as_string


# Found a noun phrase, preprocess it and add to noun phrases
# of this review
def process_found_named_entity(named_entity, stop, review_chunks_as_string):
    named_entity = named_entity.lower()
    new_entity = ''

    for token in word_tokenize(named_entity):
        if token not in stop:
            token = lemmatizer.lemmatize(token)
            if new_entity != '':
                new_entity += ' '
            new_entity += token

    if new_entity != '':
        if review_chunks_as_string != '':
            review_chunks_as_string += ','
        review_chunks_as_string += new_entity

    return review_chunks_as_string


def save_most_popular_phrases(df: pd.DataFrame, threshold: int, file_name: str):
    token_count_dict = dict()
    for index, row in df.iterrows():
        if row['preprocessedReviewChunks'] != '':
            splits = str(row['preprocessedReviewChunks']).split(',')
            for chunk in splits:
                # Filter phrases of 2 length (exclude phrases containing head and phone words)
                chunk_terms = chunk.split(' ')
                if len(chunk_terms) == 2 and ('head' not in chunk and 'phone' not in chunk):
                    if chunk in token_count_dict.keys():
                        token_count_dict[chunk] += 1
                    else:
                        token_count_dict[chunk] = 1

    filtered_dict = dict()
    for key in token_count_dict.keys():
        if token_count_dict[key] > threshold:
            filtered_dict[key] = token_count_dict[key]

    # Find swapped phrases and merge them]
    sorted_keys = sorted(filtered_dict.items(), key=lambda kv: kv[1], reverse=True)
    processed_keys = set()
    for element in sorted_keys:
        key = element[0]

        # If key is already processed as swapped chunk, do not process again
        if key in processed_keys:
            continue

        processed_keys.add(key)
        chunk_terms = key.split(' ')
        swapped_chunk = chunk_terms[1] + ' ' + chunk_terms[0]

        # If swapped version is also in dictionary, add its value to earlier one
        if swapped_chunk in filtered_dict.keys():
            processed_keys.add(swapped_chunk)
            filtered_dict[key] += filtered_dict[swapped_chunk]
            filtered_dict.pop(swapped_chunk)

    f = open(file_name, "w")
    for element in sorted(filtered_dict.items(), key=lambda kv: kv[1], reverse=True):
        f.write(str(str(element[0]) + ':' + str(element[1]) + '\n'))
    f.close()


# Preprocessing steps:
# For each review in dataset:
# - Lemmatize each word and save this version of the reviews
# - For each sentence find named entities
#   - For each named entity
#     - Remove stopwords and lemmatize the named entity
#   Save each of these chunks as concatenated string separated by comma.
if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    review_dataset_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_CSV_PATH)
    preprocessed_file_path = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

    reviews_df = cu.read_dataset(review_dataset_file_name)

    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    lemmatizer = WordNetLemmatizer()

    preprocess_and_save(reviews_df, lemmatizer, preprocessed_file_path)

    popular_phrases_file_name = os.path.join(dirname, Config.POPULAR_PHRASES_TXT_PATH)
    save_most_popular_phrases(reviews_df, 50, popular_phrases_file_name)
