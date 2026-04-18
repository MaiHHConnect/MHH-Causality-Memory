#!/usr/bin/env python3
"""
GBrain Python Port — SiliconFlow Qwen3-Embedding-8B
Schema compatible with original gbrain brain.db
"""

import sqlite3
import os
import sys
import re
import hashlib
import json
import requests
from datetime import datetime
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────

GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.join(os.path.dirname(__file__), "brain.db"))
SILICONFLOW_API = "https://api.siliconflow.cn/v1"
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
EMBEDDING_DIM = 1024  # Qwen3-Embedding-8B 输出维度

# ── DB Init ─────────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(GBRAIN_DB), exist_ok=True)
    conn = sqlite3.connect(GBRAIN_DB)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn

def _init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT UNIQUE NOT NULL,
            type        TEXT DEFAULT 'note',
            title       TEXT,
            compiled_truth TEXT,
            timeline    TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS page_fts (
            page_id     INTEGER PRIMARY KEY,
            slug        TEXT,
            title       TEXT,
            body        TEXT,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS page_fts_idx USING fts5(
            slug, title, body, content=page_fts, content_rowid=page_id
        );

        CREATE TABLE IF NOT EXISTS page_embeddings (
            page_id     INTEGER PRIMARY KEY,
            embedding   BLOB,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_page   INTEGER,
            to_slug     TEXT,
            FOREIGN KEY (from_page) REFERENCES pages(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tags (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id     INTEGER,
            tag         TEXT,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_page);
        CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_slug);
        CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
    """)

# ── Embeddings ──────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    """Call SiliconFlow Qwen3-Embedding-8B API"""
    if not SILICONFLOW_KEY:
        raise RuntimeError("SILICONFLOW_API_KEY not set")

    resp = requests.post(
        f"{SILICONFLOW_API}/embeddings",
        headers={"Authorization": f"Bearer {SILICONFLOW_KEY}", "Content-Type": "application/json"},
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]

def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = (sum(x * x for x in a) ** 0.5) * (sum(x * x for x in b) ** 0.5)
    return dot / norm if norm else 0.0

# ── Markdown parsing ──────────────────────────────────────────────────────────

def extract_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown by ## headers, returns [(header, body), ...]"""
    parts = re.split(r'(?:^|\n)(## [^#][^\n]*)\n', content)
    chunks = []
    if parts[0].strip():
        chunks.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        header = parts[i].replace("## ", "").strip() if parts[i] else ""
        body = parts[i+1].strip() if i+1 < len(parts) else ""
        if body:
            chunks.append((header, body))
    return chunks

def extract_links(content: str) -> list[str]:
    """Extract wikilinks [[slug]] and markdown links"""
    wl = re.findall(r'\[\[([^\]]+)\]\]', content)
    ml = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
    return [l.lower().replace(" ", "-") for l in wl + ml]

def build_compiled_truth(sections: list[tuple[str, str]]) -> str:
    """Build 'above the line' compiled truth from sections"""
    lines = []
    for header, body in sections:
        if header:
            lines.append(f"## {header}")
        # Take first paragraph as the truth
        first_para = body.split("\n\n")[0].strip()
        if first_para:
            lines.append(first_para)
    return "\n\n".join(lines)

def build_timeline(sections: list[tuple[str, str]]) -> str:
    """Build 'below the line' append-only timeline"""
    entries = []
    for header, body in sections:
        meta = f"## {header}" if header else "## (intro)"
        entries.append(meta)
        entries.append(body)
    return "\n\n".join(entries)

# ── Core Operations ──────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))

def put_page(slug: str, content: str, page_type: str = "note", title: Optional[str] = None):
    """Create or update a page with compiled truth + timeline"""
    conn = get_db()
    cursor = conn.cursor()

    sections = extract_sections(content)
    compiled = build_compiled_truth(sections)
    timeline = build_timeline(sections)
    title = title or sections[0][1].split("\n")[0][:80] if sections else slug

    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO pages (slug, type, title, compiled_truth, timeline, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            type=excluded.type, title=excluded.title,
            compiled_truth=excluded.compiled_truth, timeline=excluded.timeline,
            updated_at=excluded.updated_at
    """, (slug, page_type, title, compiled, timeline, now))

    page_id = cursor.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone()[0]

    # Update FTS
    cursor.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    cursor.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                   (page_id, slug, title, content))

    # Update links
    cursor.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        cursor.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))

    conn.commit()

    # Embed asynchronously (compute + store)
    _embed_page_async(page_id, compiled + "\n\n" + timeline)

    return page_id

def _embed_page_async(page_id: int, text: str):
    """Compute and store embedding for a page"""
    try:
        emb = get_embedding(text[:3000])  # truncate
        conn = get_db()
        cursor = conn.cursor()
        emb_bytes = bytes(_float32_to_bytes(emb))
        cursor.execute("DELETE FROM page_embeddings WHERE page_id=?", (page_id,))
        cursor.execute("INSERT INTO page_embeddings (page_id, embedding) VALUES (?,?)",
                       (page_id, emb_bytes))
        conn.commit()
    except Exception as e:
        print(f"[gbrain] embedding failed for page {page_id}: {e}", file=sys.stderr)

def _float32_to_bytes(vec: list[float]) -> bytes:
    import struct
    return b"".join(struct.pack("f", v) for v in vec)

# ── Search ───────────────────────────────────────────────────────────────────

def search_fts(query: str, limit: int = 10) -> list[dict]:
    """FTS5 full-text search"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        rows = cursor.execute("""
            SELECT page_id, slug, title, snippet(page_fts_idx, 2, '**', '**', '...', 30) AS snippet
            FROM page_fts_idx WHERE page_fts_idx MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []

def query_vector(question: str, limit: int = 5) -> list[dict]:
    """Vector semantic search"""
    try:
        q_emb = get_embedding(question)
    except Exception as e:
        print(f"[gbrain] query embedding failed: {e}", file=sys.stderr)
        return []

    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT page_id, embedding FROM page_embeddings").fetchall()

    results = []
    for page_id, emb_bytes in rows:
        emb = list(_bytes_to_float32(emb_bytes))
        sim = cosine_sim(q_emb, emb)
        page = cursor.execute("SELECT slug, title FROM pages WHERE id=?", (page_id,)).fetchone()
        if page:
            results.append({"page_id": page_id, "slug": page["slug"], "title": page["title"], "score": sim})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def _bytes_to_float32(data: bytes) -> list[float]:
    import struct
    return list(struct.unpack(f"{len(data)//4}f", data))

# ── CLI Commands ─────────────────────────────────────────────────────────────

def cmd_init():
    conn = get_db()
    print(f"Initialized: {GBRAIN_DB}")

def cmd_put(slug: str, filepath: Optional[str] = None):
    if filepath:
        with open(filepath) as f:
            content = f.read()
    else:
        content = sys.stdin.read()
    page_id = put_page(slug, content)
    print(f"Saved: {slug} (id={page_id})")

def cmd_get(slug: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM pages WHERE slug=?", (slug,)).fetchone()
    if not row:
        print(f"Not found: {slug}")
        return
    print(f"# {row['title'] or row['slug']}")
    print(f"\n## Compiled Truth\n{row['compiled_truth'] or '(empty)'}")
    print(f"\n## Timeline\n{row['timeline'] or '(empty)'}")

def cmd_search(query: str, limit: int = 10):
    results = search_fts(query, limit)
    if not results:
        print("(no FTS results)")
    for r in results:
        print(f"  [{r['slug']}] {r['title']}")
        if r.get('snippet'):
            print(f"    {r['snippet']}")

def cmd_query(question: str, limit: int = 5):
    results = query_vector(question, limit)
    if not results:
        print("(no vector results)")
    for r in results:
        print(f"  [{r['slug']}] {r['title']} (score={r['score']:.3f})")

def cmd_stats():
    conn = get_db()
    cur = conn.cursor()
    pages = cur.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    embeddings = cur.execute("SELECT COUNT(*) FROM page_embeddings").fetchone()[0]
    links = cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    print(f"pages: {pages}")
    print(f"embeddings: {embeddings}")
    print(f"links: {links}")

def cmd_ingest(dirpath: str):
    """Ingest all .md files from a directory"""
    import glob
    count = 0
    for filepath in glob.glob(os.path.join(dirpath, "**/*.md"), recursive=True):
        slug = slugify(os.path.splitext(os.path.basename(filepath))[0])
        try:
            put_page(slug, open(filepath).read())
            count += 1
        except Exception as e:
            print(f"  skipped {filepath}: {e}", file=sys.stderr)
    print(f"Ingested {count} files")

def cmd_list(limit: int = 20, page_type: Optional[str] = None):
    conn = get_db()
    query = "SELECT slug, type, title, updated_at FROM pages"
    params = []
    if page_type:
        query += " WHERE type=?"
        params.append(page_type)
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    for row in conn.execute(query, params).fetchall():
        print(f"  [{row['type']}] {row['slug']} — {row['title'] or ''}")

# ── Main ─────────────────────────────────────────────────────────────────────

USAGE = f"""
gbrain.py — GBrain Python Port (SiliconFlow)

Commands:
  init                      Initialize brain.db
  put <slug> [file.md]      Create/update a page
  get <slug>                Show compiled truth + timeline
  search <query>            FTS5 full-text search
  query <question>          Vector semantic search
  ingest <dir>              Bulk ingest .md files
  list [--type TYPE]        List pages
  stats                     Show statistics

Environment:
  GBRAIN_DB={GBRAIN_DB}
  SILICONFLOW_API_KEY=<your-key>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "put":
        if len(sys.argv) < 3:
            print("Usage: gbrain put <slug> [file.md]")
            sys.exit(1)
        filepath = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_put(sys.argv[2], filepath)
    elif cmd == "get":
        cmd_get(sys.argv[2])
    elif cmd == "search":
        cmd_search(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "query":
        cmd_query(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "ingest":
        cmd_ingest(sys.argv[2] if len(sys.argv) > 2 else ".")
    elif cmd == "list":
        cmd_list()
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
