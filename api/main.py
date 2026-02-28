import os
import json
import sqlite3
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from preprocess.nlp_mtl_preprocess import NLP_MTL_Preprocess
from preprocess.mtl_preprocess import MTL_Preprocess
from preprocess.tokenizer.fugashi_tokenizer import FugashiTokenizer
from preprocess.tokenizer.sudachi_tokenizer import SudachiTokenizer
from preprocess.tokenizer.spacy_tokenizer import SpacyTokenizer
from preprocess.tagger import Tagger
from api.db import init_db, get_db_connection

app = FastAPI(title="Fukuin Preprocessor API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Cache for tokenizers to avoid reloading expensive models
tokenizer_cache = {}

class BasicPreprocessRequest(BaseModel):
    text: str
    replacement_table: Dict[str, Any]
    single_kanji_filter: bool = True
    verbose: bool = False

class NLPPreprocessRequest(BaseModel):
    text: str
    replacement_table: Dict[str, Any]
    tokenizer: str = "spacy"  # spacy, sudachi, fugashi
    tag_potential_proper_nouns: bool = False
    use_user_dict: bool = False
    user_dic_path: Optional[str] = None
    use_single_kanji_filter: bool = False
    verbose: bool = False

class PreprocessResponse(BaseModel):
    text: str
    total_replacements: int

class DictionaryModel(BaseModel):
    id: int
    name: str
    is_default: bool
    content: str
    created_at: str
    updated_at: str

class CreateDictionaryRequest(BaseModel):
    name: str
    content: str

class UpdateDictionaryRequest(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

def get_tokenizer(tokenizer_name: str, use_user_dict: bool, user_dic_path: Optional[str]):
    cache_key = (tokenizer_name, use_user_dict, user_dic_path)
    if cache_key in tokenizer_cache:
        return tokenizer_cache[cache_key]

    if tokenizer_name == "fugashi":
        if use_user_dict and user_dic_path:
            tokenizer = FugashiTokenizer(user_dic_path=user_dic_path)
        else:
            tokenizer = FugashiTokenizer()
    elif tokenizer_name == "sudachi":
        if use_user_dict and user_dic_path:
            tokenizer = SudachiTokenizer(user_dic_path=user_dic_path)
        else:
            tokenizer = SudachiTokenizer()
    elif tokenizer_name == "spacy":
        if use_user_dict and user_dic_path:
            tokenizer = SpacyTokenizer(user_dic_path=user_dic_path)
        else:
            tokenizer = SpacyTokenizer()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported tokenizer: {tokenizer_name}")
    
    tokenizer_cache[cache_key] = tokenizer
    return tokenizer

@app.post("/preprocess/basic", response_model=PreprocessResponse)
async def preprocess_basic(request: BasicPreprocessRequest):
    try:
        preprocess = MTL_Preprocess(
            text=request.text,
            replacement=request.replacement_table,
            verbose=request.verbose,
            single_kanji_filter=request.single_kanji_filter
        )
        preprocessed_text = preprocess.replace()
        return PreprocessResponse(
            text=preprocessed_text,
            total_replacements=preprocess.total_replacements
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preprocess/nlp", response_model=PreprocessResponse)
async def preprocess_nlp(request: NLPPreprocessRequest):
    try:
        tokenizer = get_tokenizer(request.tokenizer, request.use_user_dict, request.user_dic_path)
        
        proper_noun_list = NLP_MTL_Preprocess.generate_name_list_from_replacement_table(request.replacement_table)
        
        tagger = Tagger(
            tokenizer=tokenizer,
            tag_potential_proper_nouns=request.tag_potential_proper_nouns,
            proper_noun_list=proper_noun_list,
        )
        
        preprocess = NLP_MTL_Preprocess(
            text=request.text,
            tagger=tagger,
            replacement_table=request.replacement_table,
            verbose=request.verbose,
            single_kanji_filter=request.use_single_kanji_filter
        )
        
        preprocessed_text = preprocess.replace()
        return PreprocessResponse(
            text=preprocessed_text,
            total_replacements=preprocess.total_replacements
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Dictionary Endpoints
@app.get("/dictionaries", response_model=List[DictionaryModel])
async def list_dictionaries():
    conn = get_db_connection()
    dictionaries = conn.execute('SELECT * FROM dictionaries').fetchall()
    conn.close()
    return [dict(ix) for ix in dictionaries]

@app.get("/dictionaries/{id}", response_model=DictionaryModel)
async def get_dictionary(id: int):
    conn = get_db_connection()
    dictionary = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
    conn.close()
    if dictionary is None:
        raise HTTPException(status_code=404, detail="Dictionary not found")
    return dict(dictionary)

@app.post("/dictionaries", response_model=DictionaryModel)
async def create_dictionary(request: CreateDictionaryRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO dictionaries (name, content) VALUES (?, ?)',
            (request.name, request.content)
        )
        dict_id = cursor.lastrowid
        conn.commit()
        dictionary = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (dict_id,)).fetchone()
        return dict(dictionary)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Dictionary with this name already exists")
    finally:
        conn.close()

@app.put("/dictionaries/{id}", response_model=DictionaryModel)
async def update_dictionary(id: int, request: UpdateDictionaryRequest):
    conn = get_db_connection()
    dictionary = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
    if dictionary is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Dictionary not found")
    
    # Optional: Prevent editing default dictionary content directly, but user asked to be able to make changes.
    # The user said: "Yes, bundle the default file, I should be able to make changes to it"
    
    update_fields = []
    params = []
    if request.name:
        update_fields.append("name = ?")
        params.append(request.name)
    if request.content:
        update_fields.append("content = ?")
        params.append(request.content)
    
    if not update_fields:
         conn.close()
         return dict(dictionary)

    update_fields.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(id)

    query = f"UPDATE dictionaries SET {', '.join(update_fields)} WHERE id = ?"
    
    try:
        conn.execute(query, params)
        conn.commit()
        updated_dict = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
        return dict(updated_dict)
    except sqlite3.IntegrityError:
         raise HTTPException(status_code=400, detail="Dictionary name conflict")
    finally:
        conn.close()

@app.put("/dictionaries/{id}/set-default", response_model=DictionaryModel)
async def set_default_dictionary(id: int):
    conn = get_db_connection()
    dictionary = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
    if dictionary is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Dictionary not found")

    try:
        conn.execute('UPDATE dictionaries SET is_default = 0')
        conn.execute('UPDATE dictionaries SET is_default = 1 WHERE id = ?', (id,))
        conn.commit()
        updated = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
        return dict(updated)
    finally:
        conn.close()

@app.delete("/dictionaries/{id}")
async def delete_dictionary(id: int):
    conn = get_db_connection()
    dictionary = conn.execute('SELECT * FROM dictionaries WHERE id = ?', (id,)).fetchone()
    if dictionary is None:
         conn.close()
         raise HTTPException(status_code=404, detail="Dictionary not found")
    
    if dictionary['is_default']:
         conn.close()
         raise HTTPException(status_code=400, detail="Cannot delete default dictionary")

    conn.execute('DELETE FROM dictionaries WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
