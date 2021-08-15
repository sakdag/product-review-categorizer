import pandas as pd

from src.config.config import Config

if __name__ == '__main__':
    reviews = pd.read_csv(Config.HEADPHONES_REVIEWS_CSV_PATH)

    print('# of Reviews:', len(reviews))
    print('# of Products:', len(reviews.groupby('asin')))
    print('# of Reviews per Product:', reviews.groupby('asin').sum()['overall'].values.mean())

    # Calculate the average number of words for each review
    word_count_list = list(map(lambda review: len(review.split()), reviews['reviewText'].values.tolist()))
    # Calculate the average length of words for each review
    avg_word_length_list = list(map(lambda review: sum(list(map(lambda word: len(word), review.split()))) / len(review.split()), reviews['reviewText'].values.tolist()))

    print('# of Words per Review:', sum(word_count_list) / len(word_count_list))
    print('Avg. Word Length:', sum(avg_word_length_list) / len(avg_word_length_list))
