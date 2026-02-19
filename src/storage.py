import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/patents.db")


def init_db():
    """Create the database and all tables if they don't exist."""
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            pub_id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            abstract TEXT,
            date TEXT,
            authors TEXT,
            venue TEXT,
            citation_count INTEGER,
            url TEXT
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


def save_publications(publications: list[dict]):
    """Insert publications into the database, ignoring duplicates."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0
    for p in publications:
        cursor.execute("""
            INSERT OR IGNORE INTO publications
            (pub_id, source, title, abstract, date, authors, venue, citation_count, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("pub_id"),
            p.get("source"),
            p.get("title"),
            p.get("abstract"),
            p.get("date"),
            p.get("authors"),
            p.get("venue"),
            p.get("citation_count", 0),
            p.get("url")
        ))
        if cursor.rowcount > 0:
            new_count += 1
    conn.commit()
    conn.close()
    print(f"Saved {new_count} new publications to database ({len(publications) - new_count} duplicates ignored).")
    return new_count


def load_patents() -> pd.DataFrame:
    """Load all patents from the database into a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM patents", conn)
    conn.close()
    return df


def load_publications(source: str = None) -> pd.DataFrame:
    """
    Load publications from the database into a DataFrame.

    Args:
        source: Optional filter - 'arxiv', 'semantic_scholar', or None for all
    """
    conn = sqlite3.connect(DB_PATH)
    if source:
        df = pd.read_sql_query(
            "SELECT * FROM publications WHERE source = ?", conn, params=(source,)
        )
    else:
        df = pd.read_sql_query("SELECT * FROM publications", conn)
    conn.close()
    return df