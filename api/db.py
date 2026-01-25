import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = "fukuin.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if empty
    cursor.execute('SELECT count(*) FROM dictionaries')
    count = cursor.fetchone()[0]
    
    if count == 0:
        seed_db(cursor)
        
    conn.commit()
    conn.close()

def seed_db(cursor):
    # Try to load rezero.json
    # Assuming api/db.py is one level down from root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rezero_path = os.path.join(root_dir, 'replacement_table', 'rezero.json')
    
    if os.path.exists(rezero_path):
        try:
            with open(rezero_path, 'r', encoding='utf-8') as f:
                # Validate JSON
                content_obj = json.load(f)
                content_str = json.dumps(content_obj, ensure_ascii=False)
                
                cursor.execute(
                    'INSERT INTO dictionaries (name, is_default, content) VALUES (?, ?, ?)',
                    ('Re:Zero Default', True, content_str)
                )
                print("Seeded Re:Zero Default dictionary.")
        except Exception as e:
            print(f"Error seeding database: {e}")
    else:
        print(f"Warning: Could not find {rezero_path} for seeding.")
