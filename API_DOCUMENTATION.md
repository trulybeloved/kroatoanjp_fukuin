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
