import os
import sqlite3
import json
import networkx as nx

DB_FILE = "knowledge_graph.db"

def create_database():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE graph_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

def save_graph_to_db(graph):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    graph_data = json.dumps(nx.node_link_data(graph))
    cursor.execute("INSERT OR REPLACE INTO graph_data (id, data) VALUES (1, ?)", (graph_data,))
    conn.commit()
    conn.close()

def load_graph_from_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM graph_data WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        graph_data = json.loads(result[0])
        return nx.node_link_graph(graph_data)
    else:
        return nx.Graph()

def save_response(
    architecture_name,
    provider,
    model,
    user_text,
    front_content,
    back_content,
    system_prompt,
):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO versioned_responses
        (architecture_name, provider, model, user_text, front_content, back_content, system_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            architecture_name,
            provider,
            model,
            user_text,
            front_content,
            back_content,
            system_prompt,
        ),
    )
    conn.commit()
    conn.close()
