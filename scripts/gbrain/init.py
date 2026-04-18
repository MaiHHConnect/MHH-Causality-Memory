#!/usr/bin/env python3
"""gbrain init"""
import sqlite3, os
GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.join(os.path.dirname(__file__), "brain.db"))
os.makedirs(os.path.dirname(GBRAIN_DB), exist_ok=True)
conn = sqlite3.connect(GBRAIN_DB)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE NOT NULL,
        type TEXT DEFAULT 'note', title TEXT,
        compiled_truth TEXT, timeline TEXT,
        created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS page_fts (
        page_id INTEGER PRIMARY KEY, slug TEXT, title TEXT, body TEXT,
        FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS page_fts_idx USING fts5(
        slug, title, body, content=page_fts, content_rowid=page_id
    );
    CREATE TABLE IF NOT EXISTS page_embeddings (
        page_id INTEGER PRIMARY KEY, embedding BLOB,
        FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT, from_page INTEGER, to_slug TEXT,
        FOREIGN KEY (from_page) REFERENCES pages(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT, page_id INTEGER, tag TEXT,
        FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);
    CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_page);
    CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_slug);
    CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);
    CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
""")
conn.close()
print(f"Initialized: {GBRAIN_DB}")
