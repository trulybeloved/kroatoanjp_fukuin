import os
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from preprocess.nlp_mtl_preprocess import NLP_MTL_Preprocess
from preprocess.mtl_preprocess import MTL_Preprocess
from preprocess.tokenizer.fugashi_tokenizer import FugashiTokenizer
from preprocess.tokenizer.sudachi_tokenizer import SudachiTokenizer
from preprocess.tokenizer.spacy_tokenizer import SpacyTokenizer
from preprocess.tagger import Tagger

app = FastAPI(title="Fukuin Preprocessor API")

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
