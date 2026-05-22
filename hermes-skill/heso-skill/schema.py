#!/usr/bin/env python3
import sqlite3, os

BASE = os.path.expanduser("~/.hermes/autoloop")
DB   = os.path.join(BASE, "progress.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS todo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    detail      TEXT,
    priority    INTEGER NOT NULL DEFAULT 3,
    status      TEXT    NOT NULL DEFAULT 'new',
    source      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS idea (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT,
    content     TEXT    NOT NULL,
    promoted    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_experience (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    observation TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS painpoint (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT    NOT NULL,
    severity    INTEGER NOT NULL DEFAULT 3,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS concept (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT    NOT NULL,
    keywords    TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS keyword_pool (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    word        TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_todo_status ON todo(status, priority);
CREATE INDEX IF NOT EXISTS idx_idea_promoted ON idea(promoted);
"""

if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Created: {DB}")