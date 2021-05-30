from nltk import word_tokenize

WARNING = '\033[93m'
ENDC = '\033[0m'


class SearchResult:
    def __init__(self,
                 review_id: int,
                 review_text: str,
                 product_id: str,
                 ranking_score: float,
                 highlight_indices: []):
        self.review_id = review_id
        self.review_text = review_text
        self.product_id = product_id
        self.ranking_score = ranking_score
        self.highlight_indices = highlight_indices

    def __str__(self):
        result = 'Review: ' + str(self.review_id)
        result += ' with score: ' + str(self.ranking_score)
        result += ' for product: ' + self.product_id + '\n'
        review_tokens = word_tokenize(self.review_text)
        highlight = 0
        for i in range(len(review_tokens)):
            for highlight_index in self.highlight_indices:
                if highlight_index[0] == i:
                    highlight = 2
                    result += WARNING
                    for j in range(highlight_index[1]):
                        result += review_tokens[i] + ' '
                        i += 1
                    result += ENDC
            if highlight == 0:
                result += review_tokens[i] + ' '
            else:
                highlight -= 1
        result += '\n'
        return result
