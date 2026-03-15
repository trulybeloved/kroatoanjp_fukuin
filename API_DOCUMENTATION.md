# Fukuin Preprocessor API Documentation

The Fukuin Preprocessor API provides a RESTful interface to the Japanese text preprocessing functions used for Machine Translation (MTL). It supports both simple string replacement and advanced NLP-based tokenization replacement.

## Base URL

- **Local**: `http://localhost:8000`
- **Docker**: `http://localhost:8000`

## Interactive Documentation

FastAPI automatically generates interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Endpoints

### 1. Health Check
Checks if the API server is up and running.

- **URL**: `/health`
- **Method**: `GET`
- **Response**:
    - `200 OK`: `{"status": "ok"}`

### 2. Basic Preprocess
Simple string-based replacement based on a provided replacement table.

- **URL**: `/preprocess/basic`
- **Method**: `POST`
- **Request Body**:
    - `text` (string): The Japanese text to preprocess.
    - `replacement_table` (object): A JSON object containing replacement rules (see below).
    - `single_kanji_filter` (boolean, optional, default: `true`): If true, skips replacement for single character names unless they have an honorific.
    - `verbose` (boolean, optional, default: `false`): Enables detailed logging on the server.
- **Response Body**:
    - `text` (string): The preprocessed text.
    - `total_replacements` (integer): Number of replacements made.

**Example Request (`curl`)**:
```bash
curl -X POST "http://localhost:8000/preprocess/basic" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "菜月昴はエミリアを愛している。",
           "replacement_table": {
             "names": {
               "Natsuki Subaru": ["菜月", "昴"],
               "Emilia": "エミリア"
             },
             "honorifics": {
               "様": "sama"
             }
           }
         }'
```

### 3. NLP Preprocess
Advanced tokenization-aware replacement. Uses a Japanese tokenizer to identify word boundaries and parts of speech (like proper nouns) to avoid over-replacement.

- **URL**: `/preprocess/nlp`
- **Method**: `POST`
- **Request Body**:
    - `text` (string): The Japanese text to preprocess.
    - `replacement_table` (object): A JSON object containing replacement rules.
    - `tokenizer` (string, optional, default: `"spacy"`): One of `spacy`, `sudachi`, or `fugashi`.
    - `tag_potential_proper_nouns` (boolean, optional, default: `false`): If true, attempts to subdivide katakana words that likely contain names.
    - `use_user_dict` (boolean, optional, default: `false`): If true, uses a user dictionary for tokenization.
    - `user_dic_path` (string, optional): Path to the user dictionary file on the server.
    - `use_single_kanji_filter` (boolean, optional, default: `false`): If true, skips replacement for single character names.
    - `verbose` (boolean, optional, default: `false`): Enables detailed logging on the server.
- **Response Body**:
    - `text` (string): The preprocessed text.
    - `total_replacements` (integer): Number of replacements made.

**Example Request (`curl`)**:
```bash
curl -X POST "http://localhost:8000/preprocess/nlp" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "菜月昴はエミリアを愛している。",
           "replacement_table": {
             "names": {
               "Natsuki Subaru": ["菜月", "昴"],
               "Emilia": "エミリア"
             }
           },
           "tokenizer": "sudachi"
         }'
```

### 4. Tokenize
Tokenizes a Japanese sentence and returns morphological analysis for each token: surface text, English part-of-speech label, lemma (dictionary form), katakana reading, and the raw Unidic POS tag.

This endpoint is useful for inspecting how the tokenizer sees a sentence before running it through the preprocessor, or for any downstream task that needs structured linguistic data.

- **URL**: `/tokenize`
- **Method**: `POST`
- **Request Body**:
    - `sentence` (string): The Japanese sentence to tokenize.
    - `tokenizer` (string, optional, default: `"spacy"`): Tokenizer to use. Accepted values: `spacy`, `sudachi`.
- **Response Body**:
    - `tokenizer` (string): The tokenizer that was used.
    - `tokens` (array): Ordered list of token objects, one per morpheme. Each token contains:
        - `text` (string): Surface form of the token as it appears in the input.
        - `pos` (string): English part-of-speech label (see [POS label reference](#pos-label-reference) below).
        - `lemma` (string | null): Dictionary/base form of the token (e.g. `食べた` → `食べる`).
        - `reading` (string | null): Katakana reading of the token (e.g. `東京` → `トウキョウ`).
        - `raw_pos` (string | null): Raw Unidic POS tag, hyphen-delimited (e.g. `名詞-固有名詞-地名-一般`).

**Example Request (`curl`)**:
```bash
curl -X POST "http://localhost:8000/tokenize" \
     -H "Content-Type: application/json" \
     -d '{
           "sentence": "東京に行きます。",
           "tokenizer": "spacy"
         }'
```

**Example Response**:
```json
{
  "tokenizer": "spacy",
  "tokens": [
    {
      "text": "東京",
      "pos": "Proper Noun",
      "lemma": "東京",
      "reading": "トウキョウ",
      "raw_pos": "名詞-固有名詞-地名-一般"
    },
    {
      "text": "に",
      "pos": "Particle",
      "lemma": "に",
      "reading": "ニ",
      "raw_pos": "助詞-格助詞"
    },
    {
      "text": "行き",
      "pos": "Verb",
      "lemma": "行く",
      "reading": "イキ",
      "raw_pos": "動詞-一般"
    },
    {
      "text": "ます",
      "pos": "Auxiliary Verb",
      "lemma": "ます",
      "reading": "マス",
      "raw_pos": "助動詞"
    },
    {
      "text": "。",
      "pos": "Punctuation",
      "lemma": "。",
      "reading": "。",
      "raw_pos": "補助記号-句点"
    }
  ]
}
```

#### Tokenizer Differences

| Feature | `spacy` | `sudachi` |
|---|---|---|
| POS source | spaCy's neural model (Universal POS mapped to English) | Unidic dictionary tags (mapped to English) |
| Reading source | `morph` features from spaCy | `reading_form()` from SudachiPy |
| Lemma source | `lemma_` from spaCy | `dictionary_form()` from SudachiPy |
| Raw POS format | Full Unidic tag string (from underlying Sudachi) | Hyphen-joined Unidic fields, wildcards stripped |
| Proper noun detection | More accurate (neural model) | Dictionary-based |

Both tokenizers use SudachiPy under the hood (spaCy wraps Sudachi), so tokenization boundaries are generally the same. The main difference is that spaCy's neural model improves proper noun identification for ambiguous cases.

---

## POS Label Reference

The `pos` field in `/tokenize` responses uses the following English labels, derived from Unidic (Sudachi) or Universal POS (spaCy) tags:

| POS Label | Japanese Unidic Equivalent | Description |
|---|---|---|
| Noun | 名詞・普通名詞 | Common noun |
| Proper Noun | 名詞・固有名詞 | Names of people, places, organisations |
| Pronoun | 代名詞 / 名詞・代名詞 | Personal and demonstrative pronouns |
| Numeral | 名詞・数詞 | Numbers and counting words |
| Verb | 動詞 | Action and state verbs |
| Adjective | 形容詞 | I-adjectives (～い) |
| Adjectival Noun | 形状詞 | Na-adjectives (～な / ～だ base) |
| Pre-noun Adjective | 連体詞 | Adnominal words that directly modify nouns (この, その, etc.) |
| Adverb | 副詞 | Adverbs modifying verbs or adjectives |
| Particle | 助詞 | Grammatical particles (は, が, を, に, etc.) |
| Auxiliary Verb | 助動詞 | Verb endings and auxiliaries (ます, た, ない, etc.) |
| Conjunction | 接続詞 | Conjunctions linking clauses |
| Interjection | 感動詞 | Exclamations and filler words |
| Prefix | 接頭辞 | Word-initial bound morphemes |
| Suffix | 接尾辞 | Word-final bound morphemes (including honorific suffixes) |
| Postposition | 助詞 (spaCy ADP) | Postpositions (spaCy path only) |
| Symbol | 記号 | Non-punctuation symbols |
| Punctuation | 補助記号 | Punctuation marks |
| Whitespace | 空白 | Whitespace tokens |
| Other | X | Unclassified tokens |

---

## Replacement Table Format

The `replacement_table` is a dictionary with specific keys:

- `names`: Important character/place names.
    - Format: `"English Name": "Japanese Name"` or `"English Name": ["Japanese", "Name"]` (for multi-part names).
- `full-names`: Full names for secondary characters.
- `last-names`: Last names only.
- `single-names`: Individual name parts.
- `name-like`: Terms that behave like names.
- `specials`: Special term replacements (not name-based).
- `basic`: General punctuation or common term replacements.
- `honorifics`: Japanese honorifics to their English romanization.
    - Format: `"様": "sama"`, `"さん": "san"`.

---

## Error Handling

The API returns standard HTTP status codes:
- `200 OK`: Success.
- `400 Bad Request`: Validation errors or unsupported tokenizer.
- `422 Unprocessable Entity`: Request format errors (Pydantic validation).
- `500 Internal Server Error`: Unexpected server-side errors.
