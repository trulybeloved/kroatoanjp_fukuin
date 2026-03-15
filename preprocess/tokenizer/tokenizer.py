from typing import Dict, List

from preprocess.sentence import Sentence

# Splits string into words which have pos tags
class Tokenizer:
    def __init__(self):
        pass

    def tokenize(self, text:str) -> Sentence:
        pass

    def analyze(self, text: str) -> List[Dict]:
        raise NotImplementedError
