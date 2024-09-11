import sqlite3
import os

DB_FILE = 'knowledge_graph.db'

def create_database():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE versioned_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                architecture_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                user_text TEXT NOT NULL,
                front_content TEXT NOT NULL,
                back_content TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def save_response(architecture_name, provider, model, user_text, front_content, back_content, system_prompt):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO versioned_responses
        (architecture_name, provider, model, user_text, front_content, back_content, system_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (architecture_name, provider, model, user_text, front_content, back_content, system_prompt))
    conn.commit()
    conn.close()
