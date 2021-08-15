import json
import string

from nltk import word_tokenize

WARNING = '\033[93m'
ENDC = '\033[0m'


class SearchResult:
    def __init__(self,
                 review_id: int,
                 review_text: str,
                 product_id: str,
                 ranking_score: float,
                 overall: int,
                 title: str,
                 image: str,
                 highlight_indices: []):
        self.review_id = review_id
        self.review_text = review_text
        self.product_id = product_id
        self.ranking_score = ranking_score
        self.overall = overall
        self.title = title
        self.image = image
        self.highlight_indices = highlight_indices

    def __str__(self):
        result = 'Review Id: ' + str(self.review_id)
        result += ' with score: ' + str(self.ranking_score)
        result += ' for product: ' + self.product_id + '\n'

        extra_index = 0
        current_review = self.review_text
        for index in self.highlight_indices:
            current_review = current_review[:index[0] + extra_index] + WARNING + current_review[index[0] + extra_index:]
            extra_index += len(WARNING)
            current_review = current_review[:index[1] + extra_index] + ENDC + current_review[index[1] + extra_index:]
            extra_index += len(ENDC)

        result += current_review
        result += '\n------------------------------------------------------------------'
        return result

    def get_json_representation(self):
        return json.dumps(self.__dict__)
