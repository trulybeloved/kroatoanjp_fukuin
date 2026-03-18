from typing import Optional, List, Dict

import fugashi

from preprocess.tokenizer.tokenizer import Tokenizer
from preprocess.sentence import Word
from preprocess.tokenizer.part_of_speech import PartOfSpeech, UNIDIC_ENGLISH_POS_MAP

class FugashiTokenizer(Tokenizer):
    def __init__(
        self, 
        user_dic_path:Optional[str] = None # Path to MeCab user dic
    ):
        if user_dic_path:
            self._tagger = fugashi.Tagger(f"-u {user_dic_path}")
        else:
            self._tagger = fugashi.Tagger()

    def tokenize(self, text:str) -> List[Word]:
        word_list = []
        tagged_words = self._tagger(text)
        for word in tagged_words:
            word_text = word.surface
            # TODO: Add an explanation of the word.feature tuple
            part_of_speech = word.feature[0]
            # Prefer the more specific proper noun pos tag when available,
            # as it enables more accurate single kanji replacement
            if word.feature[0] == PartOfSpeech.NOUN and \
                word.feature[1] == PartOfSpeech.PROPER_NOUN:
                part_of_speech = word.feature[1]
            word_list.append(Word(word_text, part_of_speech))
        return word_list

    def analyze(self, text: str) -> List[Dict]:
        results = []
        for word in self._tagger(text):
            f = word.feature
            pos1 = f.pos1 if f.pos1 and f.pos1 != "*" else None
            pos2 = f.pos2 if f.pos2 and f.pos2 != "*" else None
            pos3 = f.pos3 if f.pos3 and f.pos3 != "*" else None
            pos4 = f.pos4 if f.pos4 and f.pos4 != "*" else None
            lemma = f.lemma if f.lemma and f.lemma != "*" else None
            reading = f.kana if f.kana and f.kana != "*" else None

            raw_pos = "-".join(p for p in [pos1, pos2, pos3, pos4] if p) or None

            if pos1 == "名詞":
                if pos2 == "固有名詞":
                    pos_english = "Proper Noun"
                elif pos2 == "数詞":
                    pos_english = "Numeral"
                elif pos2 == "代名詞":
                    pos_english = "Pronoun"
                else:
                    pos_english = "Noun"
            else:
                pos_english = UNIDIC_ENGLISH_POS_MAP.get(pos1, "Other")

            results.append({
                "text": word.surface,
                "pos": pos_english,
                "lemma": lemma,
                "reading": reading,
                "raw_pos": raw_pos,
            })
        return results