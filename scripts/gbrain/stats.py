#!/usr/bin/env python3
"""gbrain stats"""
import sqlite3, json, os
GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.join(os.path.dirname(__file__), "brain.db"))
conn = sqlite3.connect(GBRAIN_DB)
conn.row_factory = sqlite3.Row
pages = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
embeddings = conn.execute("SELECT COUNT(*) FROM page_embeddings").fetchone()[0]
fts = conn.execute("SELECT COUNT(*) FROM page_fts").fetchone()[0]
result = {"pages": pages, "embeddings": embeddings, "fts_entries": fts}
print(json.dumps(result))
conn.close()
