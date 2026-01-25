import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")

def test_basic():
    payload = {
        "text": "菜月昴はエミリアを愛している。",
        "replacement_table": {
            "names": {
                "Natsuki Subaru": ["菜月", "昴"],
                "Emilia": "エミリア"
            },
            "honorifics": {
                "様": "sama",
                "さん": "san"
            }
        },
        "single_kanji_filter": True,
        "verbose": True
    }
    try:
        response = requests.post(f"{BASE_URL}/preprocess/basic", json=payload)
        print(f"Basic preprocess: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(response.text)
    except Exception as e:
        print(f"Basic preprocess failed: {e}")

def test_nlp():
    payload = {
        "text": "菜月昴はエミリアを愛している。",
        "replacement_table": {
            "names": {
                "Natsuki Subaru": ["菜月", "昴"],
                "Emilia": "エミリア"
            },
            "honorifics": {
                "様": "sama",
                "さん": "san"
            }
        },
        "tokenizer": "sudachi", # Sudachi is lighter than spacy for a quick test
        "use_single_kanji_filter": False,
        "verbose": True
    }
    try:
        response = requests.post(f"{BASE_URL}/preprocess/nlp", json=payload)
        print(f"NLP preprocess: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(response.text)
    except Exception as e:
        print(f"NLP preprocess failed: {e}")

if __name__ == "__main__":
    # Wait for server to start if running in background
    time.sleep(2)
    test_health()
    test_basic()
    test_nlp()
