import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/patents.db")

def init_db():
    """Create the database and patents table if they don't exist."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patents (
            patent_id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            date TEXT,
            assignee TEXT,
            cpc_codes TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")

def save_patents(patents: list[dict]):
    """Insert patents into the database, ignoring duplicates."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for p in patents:
        cursor.execute("""
            INSERT OR IGNORE INTO patents 
            (patent_id, title, abstract, date, assignee, cpc_codes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            p.get("patent_id"),
            p.get("patent_title"),
            p.get("patent_abstract"),
            p.get("patent_date"),
            p.get("assignee_organization"),
            p.get("cpc_codes")
        ))
    conn.commit()
    conn.close()
    print(f"Saved {len(patents)} patents to database.")

def load_patents() -> pd.DataFrame:
    """Load all patents from the database into a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM patents", conn)
    conn.close()
    return df