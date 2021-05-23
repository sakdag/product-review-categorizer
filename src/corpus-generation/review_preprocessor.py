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

                        # Found a noun phrase, preprocess it and add to noun phrases
                        # of this review
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
                            # review_chunks.append(new_entity)
                        current_chunk = []
                else:
                    continue

        df.loc[index, 'preprocessedReviewChunks'] = review_chunks_as_string

    # Save
    df.to_csv(preprocessed_file_name, index_label='reviewId')


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    review_dataset_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_CSV_PATH)
    preprocessed_file_name = os.path.join(dirname, '../data/', Config.HEADPHONES_REVIEWS_PREPROCESSED_CSV_PATH)

    df = cu.read_dataset(review_dataset_file_name)

    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    lemmatizer = WordNetLemmatizer()

    preprocess_and_save(df, lemmatizer, preprocessed_file_name)
