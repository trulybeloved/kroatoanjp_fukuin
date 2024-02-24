import os

class FukuinConfig:

    current_working_directory = os.getcwd()
    parent_directory = os.path.dirname(current_working_directory)

    tokenizer = "spacy"  # "spacy" / "sudachi" / "fugashi"
    tag_potential_proper_nouns = True
    use_user_dict = True  # SHOULD ALWAYS BE TRUE
    user_dic_path = os.path.join(parent_directory, 'data', 'dictionaries', 'rezero-sudachi.dic') # SHOULD ALWAYS BE SPECIFIED
    use_single_kanji_filter = True  # SHOULD BE TRUE UNLESS REPLACING SINGLE KANJI NAMES
    katakana_words_file_path = os.path.join(parent_directory, 'data', 'katakana_words.txt')