from enum import Enum

# Subset of the Unidic part of speech tags, as listed:
# https://gist.github.com/masayu-a/e3eee0637c07d4019ec9
class PartOfSpeech(str, Enum):
    NOUN = "名詞"
    PROPER_NOUN = "固有名詞"
    PUNCTUATION = "補助記号"
    WHITESPACE = "空白"

# Maps primary Unidic POS to English grammar terms.
# Subtypes (e.g. 固有名詞, 数詞) are resolved separately in analyze() logic.
UNIDIC_ENGLISH_POS_MAP = {
    "名詞":   "Noun",
    "動詞":   "Verb",
    "形容詞": "Adjective",
    "形状詞": "Adjectival Noun",
    "副詞":   "Adverb",
    "助詞":   "Particle",
    "助動詞": "Auxiliary Verb",
    "接続詞": "Conjunction",
    "感動詞": "Interjection",
    "接頭辞": "Prefix",
    "接尾辞": "Suffix",
    "記号":   "Symbol",
    "補助記号": "Punctuation",
    "空白":   "Whitespace",
    "連体詞": "Pre-noun Adjective",
    "代名詞": "Pronoun",
}

# Maps spaCy universal POS tags to English grammar terms
SPACY_ENGLISH_POS_MAP = {
    "NOUN":  "Noun",
    "PROPN": "Proper Noun",
    "VERB":  "Verb",
    "ADJ":   "Adjective",
    "ADV":   "Adverb",
    "ADP":   "Postposition",
    "AUX":   "Auxiliary Verb",
    "CCONJ": "Conjunction",
    "SCONJ": "Conjunction",
    "PART":  "Particle",
    "INTJ":  "Interjection",
    "PRON":  "Pronoun",
    "DET":   "Pre-noun Adjective",
    "NUM":   "Numeral",
    "PUNCT": "Punctuation",
    "SYM":   "Symbol",
    "SPACE": "Whitespace",
    "X":     "Other",
}