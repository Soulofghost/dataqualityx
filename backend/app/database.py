import os
import sqlite3
from backend.app.config import DB_PATH

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        row_count INTEGER,
        column_count INTEGER,
        health_score REAL,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS column_profiles (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        column_name TEXT,
        inferred_type TEXT,
        null_count INTEGER,
        completeness_pct REAL,
        distinct_count INTEGER,
        min_val TEXT,
        max_val TEXT,
        mean_val REAL,
        outliers_count INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quality_assertions (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        assertion_type TEXT,
        column_name TEXT,
        parameters TEXT,
        passed INTEGER,
        message TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_baselines (
        id TEXT PRIMARY KEY,
        dataset_name TEXT UNIQUE,
        schema_json TEXT,
        updated_at TEXT
    );
    """)

    conn.commit()
    conn.close()

init_db()
