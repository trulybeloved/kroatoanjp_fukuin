import os
import os.path
import json
from tempfile import NamedTemporaryFile
from typing import Dict, Optional, List

from sudachipy import tokenizer, dictionary

from preprocess.tokenizer.tokenizer import Tokenizer
from preprocess.sentence import Word
from preprocess.tokenizer.part_of_speech import PartOfSpeech, UNIDIC_ENGLISH_POS_MAP
from preprocess.utils import is_punctuation

class SudachiTokenizer(Tokenizer):
    def __init__(
        self, 
        user_dic_path:Optional[str] = None # Path to Sudachi user dic
    ):
        self._split_mode = tokenizer.Tokenizer.SplitMode.A
        if user_dic_path:
            self._user_dic_path = user_dic_path
            # Sudachi reads the user dictionaries that are listed in its
            # config, but requires the config be passed as a path to
            # a json file rather than being passed directly
            config_path = self._generate_temporary_sudachi_config_file()
            self._tokenizer = dictionary.Dictionary(config_path=config_path).create()
            self._delete_temporary_sudachi_config_file(config_path)
        else:
            self._tokenizer = dictionary.Dictionary().create()

    def tokenize(self, text:str) -> List[Word]:
        word_list = []
        tagged_words = self._tokenizer.tokenize(text, self._split_mode)
        for word in tagged_words:
            word_text = word.surface()
            # TODO: Add an explanation of the part_of_speech_tuple tuple
            part_of_speech_tuple = word.part_of_speech()
            part_of_speech = part_of_speech_tuple[0]
            # Some tokenizers (Sudachi, Nagisa) tend to mistag long
            # strings of punctuation
            if part_of_speech != PartOfSpeech.PUNCTUATION and \
               is_punctuation(word_text):
               part_of_speech = PartOfSpeech.PUNCTUATION
            # Prefer the more specific proper noun pos tag when available,
            # as it enables more accurate single kanji replacement
            elif part_of_speech_tuple[0] == PartOfSpeech.NOUN and \
                 part_of_speech_tuple[1] == PartOfSpeech.PROPER_NOUN:
                part_of_speech = part_of_speech_tuple[1]
            word_list.append(Word(word_text, part_of_speech))
        return word_list

    def analyze(self, text: str) -> List[Dict]:
        results = []
        for word in self._tokenizer.tokenize(text, self._split_mode):
            pos_tuple = word.part_of_speech()
            raw_pos = "-".join(p for p in pos_tuple[:4] if p and p != "*")
            primary = pos_tuple[0]
            secondary = pos_tuple[1] if len(pos_tuple) > 1 else "*"
            if primary == "名詞":
                if secondary == "固有名詞":
                    pos_english = "Proper Noun"
                elif secondary == "数詞":
                    pos_english = "Numeral"
                elif secondary == "代名詞":
                    pos_english = "Pronoun"
                else:
                    pos_english = "Noun"
            else:
                pos_english = UNIDIC_ENGLISH_POS_MAP.get(primary, "Other")
            results.append({
                "text": word.surface(),
                "pos": pos_english,
                "lemma": word.dictionary_form(),
                "reading": word.reading_form(),
                "raw_pos": raw_pos,
            })
        return results

    def _generate_temporary_sudachi_config_file(self) -> str:
        sudachi_config = {
            "userDict": [self._user_dic_path],
            "oovProviderPlugin": [
                {
                    "class": "com.worksap.nlp.sudachi.MeCabOovPlugin",
                    "charDef": "char.def",
                    "unkDef": "unk.def"
                },
                {
                    "class": "com.worksap.nlp.sudachi.SimpleOovPlugin",
                    "oovPOS": ["補助記号", "一般", "*", "*", "*", "*"],
                    "leftId": 5968,
                    "rightId": 5968,
                    "cost": 3857
                }
            ]
        }
        with NamedTemporaryFile(mode="w", delete=False) as config_file:
            config_file.write(json.dumps(sudachi_config))
        config_path = config_file.name
        return config_path

    def _delete_temporary_sudachi_config_file(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
            