import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = "fukuin.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dictionary_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dictionary_id) REFERENCES dictionaries(id) ON DELETE CASCADE
        )
    ''')
    
    # Check if empty
    cursor.execute('SELECT count(*) FROM dictionaries')
    count = cursor.fetchone()[0]
    
    if count == 0:
        seed_db(cursor)
        
    conn.commit()
    conn.close()

def save_history_entry(cursor, dictionary_id: int, content: str):
    """Save a content snapshot and prune to 500 entries per dictionary."""
    row = cursor.execute(
        'SELECT COALESCE(MAX(version_number), 0) FROM dictionary_history WHERE dictionary_id = ?',
        (dictionary_id,)
    ).fetchone()
    next_version = row[0] + 1

    cursor.execute(
        'INSERT INTO dictionary_history (dictionary_id, version_number, content) VALUES (?, ?, ?)',
        (dictionary_id, next_version, content)
    )

    # Prune: keep only the 500 most recent entries
    cursor.execute(
        '''DELETE FROM dictionary_history
           WHERE dictionary_id = ? AND id NOT IN (
               SELECT id FROM dictionary_history
               WHERE dictionary_id = ?
               ORDER BY version_number DESC
               LIMIT 500
           )''',
        (dictionary_id, dictionary_id)
    )


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
                dict_id = cursor.lastrowid
                save_history_entry(cursor, dict_id, content_str)
                print("Seeded Re:Zero Default dictionary.")
        except Exception as e:
            print(f"Error seeding database: {e}")
    else:
        print(f"Warning: Could not find {rezero_path} for seeding.")
