import json
import os
import re

from flask import Flask, request
from nltk import WordNetLemmatizer
from spellchecker import SpellChecker
from whoosh import index, qparser
from whoosh.qparser import QueryParser

import src.config.config as conf
import src.search.phrase_search as phrase_search
import src.utils.categorizer_utils as categorizer_utils
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
        limit = request.args.get('limit')
        parser_type = request.args.get('parser_type')
    else:
        phrases = request.json['phrases']
        limit = request.json['limit']
        parser_type = request.json['parser_type']

    for phrase in phrases.split(','):
        phrases_to_query.append(phrase)

    if limit is None:
        limit = 10
    else:
        limit = int(limit)

    if parser_type is None:
        parser_type = 'or_type'

    return generate_search_results(phrases_to_query, limit, parser_type)


def generate_search_results(phrases_to_query: list, limit: int, parser_type: str):
    if parser_type == 'and_type':
        qp = default_qp
    else:
        qp = or_qp

    results = phrase_search.search_for(ix, qp, phrases_to_query, limit)
    highlighted_results = phrase_search.highlight_search_terms(results, phrases_to_query, lemmatizer,
                                                               punctuation_regex, spell)

    json_result_list = list()
    for result in highlighted_results:
        json_result_list.append(result.get_json_representation())

    return json.dumps(json_result_list)


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    review_dataset_file_name = os.path.join(dirname, conf.POPULAR_PHRASES_TXT_PATH)
    index_dir = os.path.join(dirname, conf.INDEX_PATH)

    # Get popular phrases from the file
    popular_phrases_json = categorizer_utils.read_popular_phrases(review_dataset_file_name)

    lemmatizer = WordNetLemmatizer()
    punctuation_regex = re.compile(r'(([^\w\s])+)')
    spell = SpellChecker()

    # Read whoosh index
    ix = index.open_dir(index_dir)
    og = qparser.OrGroup.factory(0.9)

    default_qp = QueryParser("lemmatizedReview", schema=ix.schema)
    or_qp = QueryParser("lemmatizedReview", schema=ix.schema, group=og)

    app.run(debug=True, use_reloader=False)
