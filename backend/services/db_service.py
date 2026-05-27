import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = "projects.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            number TEXT,
            analysis_data TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_project(name: str, number: str, analysis_data: dict) -> str:
    project_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (id, name, number, analysis_data, created_at) VALUES (?, ?, ?, ?, ?)",
        (project_id, name, number, json.dumps(analysis_data, ensure_ascii=False), created_at)
    )
    conn.commit()
    conn.close()
    return project_id

def get_projects():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, number, created_at FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_project_by_id(project_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        res['analysis_data'] = json.loads(res['analysis_data'])
        return res
    return None
