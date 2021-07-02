import json
import os

from flask import Flask, request
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from whoosh import index

from src.config.config import Config
from src.search import phrase_search
from src.util import categorizer_utils

app = Flask(__name__)


@app.route("/headphones/phrases", methods=['GET'])
def get_phrases():
    return popular_phrases_json


@app.route("/headphones/search", methods=['GET', 'POST'])
def search():
    phrases_to_query = list()

    if request.method == 'GET':
        phrases = request.args.get('phrases')
    else:
        phrases = request.json['phrases']

    for phrase in phrases.split(','):
        phrases_to_query.append(phrase)

    return generate_search_results(phrases_to_query)


def generate_search_results(phrases_to_query: list):
    results = phrase_search.search_for(ix, phrases_to_query)
    highlighted_results = phrase_search.highlight_search_terms(results, phrases_to_query, stop, lemmatizer)

    json_result_list = list()
    for result in highlighted_results:
        json_result_list.append(result.get_json_representation())

    return json.dumps(json_result_list)


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    review_dataset_file_name = os.path.join(dirname, '../data/', Config.POPULAR_PHRASES_TXT_PATH)
    index_dir = os.path.join(dirname, Config.INDEX_PATH)

    # Get popular phrases from the file
    popular_phrases_json = categorizer_utils.read_popular_phrases(review_dataset_file_name)

    stop = stopwords.words('english')
    lemmatizer = WordNetLemmatizer()
    # Read whoosh index
    ix = index.open_dir(index_dir)

    app.run(debug=True, use_reloader=False)
