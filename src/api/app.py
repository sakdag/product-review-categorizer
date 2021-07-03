import json
import os
import re

from flask import Flask, request
from nltk import WordNetLemmatizer
from spellchecker import SpellChecker
from whoosh import index
from whoosh.qparser import QueryParser

from src.config.config import Config
from src.search import phrase_search
from src.util import categorizer_utils
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

    limit = int(request.args.get('limit'))
    if limit is None:
        limit = 10

    return generate_search_results(phrases_to_query, limit)


def generate_search_results(phrases_to_query: list, limit: int):
    results = phrase_search.search_for(ix, qp, phrases_to_query, limit)
    highlighted_results = phrase_search.highlight_search_terms(results, phrases_to_query, lemmatizer,
                                                               punctuation_regex, spell)

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

    lemmatizer = WordNetLemmatizer()
    punctuation_regex = re.compile(r'(([^\w\s])+)')
    spell = SpellChecker()

    # Read whoosh index
    ix = index.open_dir(index_dir)
    qp = QueryParser("lemmatizedReview", schema=ix.schema)

    app.run(debug=True, use_reloader=False)
