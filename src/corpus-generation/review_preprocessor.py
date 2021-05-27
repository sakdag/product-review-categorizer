import os
import nltk as nltk
import numpy as np
from nltk import tokenize, RegexpParser, pos_tag, word_tokenize, Tree
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer

import pandas as pd
from src.util import categorizer_utils as cu
from src.config.config import Config

# Defining a grammar & Parser
NP = "NP: {(<V\w+>|<NN\w?>)+.*<NN\w?>}"
chunker = RegexpParser(NP)


def preprocess_and_save(df: pd.DataFrame, lemmatizer, preprocessed_file_name: str):
    chunk_func = chunker.parse
    stop = stopwords.words('english')

    for index, row in df.iterrows():
        sentences = tokenize.sent_tokenize(row['reviewText'])

        review_chunks_as_string = process_review(sentences, chunk_func, stop)

        df.loc[index, 'preprocessedReviewChunks'] = review_chunks_as_string

    # Save
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


def save_most_popular_phrases(threshold: int, file_name: str):
    token_count_dict = dict()
    for index, row in df.iterrows():
        splits = str(row['preprocessedReviewChunks']).split(',')
        for chunk in splits:
            if chunk in token_count_dict.keys():
                token_count_dict[chunk] += 1
            else:
                token_count_dict[chunk] = 1

    filtered_dict = dict()
    for key in token_count_dict.keys():
        if token_count_dict[key] > threshold:
            filtered_dict[key] = token_count_dict[key]

    f = open(file_name, "w")
    for element in sorted(filtered_dict.items(), key=lambda kv: kv[1], reverse=True):
        f.write(str(str(element[0]) + ':' + str(element[1]) + '\n'))
    f.close()


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    review_dataset_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_CSV_PATH)
    preprocessed_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

    df = cu.read_dataset(preprocessed_file_name)

    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    lemmatizer = WordNetLemmatizer()

    preprocess_and_save(df, lemmatizer, preprocessed_file_name)

    popular_phrases_file_name = os.path.join(dirname, Config.POPULAR_PHRASES_TXT_PATH)
    save_most_popular_phrases(50, popular_phrases_file_name)
