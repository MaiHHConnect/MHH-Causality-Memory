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

GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.expanduser("~/gbrain-data/brain.db"))
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
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            slug            TEXT UNIQUE NOT NULL,
            type            TEXT DEFAULT 'note',
            title           TEXT,
            compiled_truth   TEXT,
            timeline        TEXT,
            -- Structured summary fields (Claude-Mem inspired)
            summary_struct  TEXT,     -- JSON: {request, investigated, learned, completed, next_steps}
            concepts        TEXT,     -- JSON array of concept tags
            decided         TEXT,     -- What was decided
            learned         TEXT,     -- What was learned
            completed       TEXT,     -- What was completed
            next_steps      TEXT,     -- Next steps
            -- Causality fields (因果推理)
            cause           TEXT,     -- 前因：导致这个事件的原因
            effect          TEXT,     -- 后果：导致的后续事件/变化
            -- Emotion field (情绪追踪)
            emotion         TEXT,     -- 情绪状态：开心|低落|饿|饱|累|精神|焦虑|专注|满足|空虚|无
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
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
    # Migration: add emotion column if it doesn't exist
    try:
        conn.execute("ALTER TABLE pages ADD COLUMN emotion TEXT DEFAULT '无'")
    except Exception:
        pass  # Column already exists

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


def query_causal(keyword: str, limit: int = 10) -> list[dict]:
    """因果检索：搜索 cause 或 effect 字段匹配的内容"""
    conn = get_db()
    rows = conn.execute("""
        SELECT slug, title, cause, effect, decided, learned
        FROM pages
        WHERE cause LIKE ? OR effect LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (f"%{keyword}%", f"%{keyword}%", limit)).fetchall()
    return [dict(r) for r in rows]


def cmd_causal(keyword: str, limit: int = 10):
    """CLI: 查询因果链"""
    results = query_causal(keyword, limit)
    if not results:
        print(f"(no causal results for: {keyword})")
        return
    for r in results:
        print(f"\n[{r['slug']}] {r['title']}")
        if r.get('cause'):
            print(f"  前因: {r['cause']}")
        if r.get('effect'):
            print(f"  后果: {r['effect']}")
        if r.get('emotion'):
            print(f"  情绪: {r['emotion']}")
        if r.get('decided'):
            print(f"  决定: {r['decided']}")

def compress_observation(raw_text: str, obs_type: str = "INSIGHT") -> dict:
    """
    AI-powered observation compression (Claude-Mem inspired + 因果推理).
    Returns structured dict: {decided, learned, completed, next_steps, concepts, cause, effect}
    """
    import requests
    api_key = os.environ.get("MINIMAX_API_KEY", "") or os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        # Fallback: simple extract
        return {
            "decided": raw_text[:100],
            "learned": "",
            "completed": "",
            "next_steps": "",
            "concepts": [],
            "cause": "",
            "effect": "",
            "summary_struct": {"type": obs_type, "raw": raw_text[:200]}
        }
    
    prompt = f"""分析以下观测记录，提取结构化信息。严格按JSON格式回复，不要有其他内容：

观测类型: {obs_type}
内容: {raw_text}

请提取：
- decided: 决定了什么（核心决策，20字内）
- learned: 学到了什么（关键收获，20字内）
- completed: 完成了什么（已解决/实现，20字内）
- next_steps: 下一步要做什么（待处理事项，20字内）
- concepts: 概念标签（2-4个中文关键词）
- cause: 前因——导致这个事件发生的原因是什么（15字内，没有则写"无"）
- effect: 后果——这个事件会导致什么后续变化（15字内，没有则写"无"）
- emotion: 当前情绪状态，从以下10种选一个：开心|低落|饿|饱|累|精神|焦虑|专注|满足|空虚|无

JSON格式：
{{"decided":"...", "learned":"...", "completed":"...", "next_steps":"...", "concepts":["...","..."], "cause":"...", "effect":"...", "emotion":"..."}}"""

    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "MiniMax-M2.5",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250
            },
            timeout=30
        )
        result = resp.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Extract JSON
        import re
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            return {
                "decided": data.get("decided", ""),
                "learned": data.get("learned", ""),
                "completed": data.get("completed", ""),
                "next_steps": data.get("next_steps", ""),
                "concepts": data.get("concepts", []),
                "cause": data.get("cause", ""),
                "effect": data.get("effect", ""),
                "emotion": data.get("emotion", "无"),
                "summary_struct": {"type": obs_type, "raw": raw_text[:500]}
            }
    except Exception as e:
        print(f"[gbrain] compress failed: {e}", file=sys.stderr)
    
    return {
        "decided": raw_text[:100],
        "learned": "",
        "completed": "",
        "next_steps": "",
        "concepts": [],
        "cause": "",
        "effect": "",
        "emotion": "无",
        "summary_struct": {"type": obs_type, "raw": raw_text[:200]}
    }


def put_page_structured(slug: str, content: str, page_type: str = "note", 
                        title: Optional[str] = None, obs_type: str = "INSIGHT"):
    """Create/update a page with AI-compressed structured summary"""
    # Compress with AI
    structured = compress_observation(content, obs_type)
    
    conn = get_db()
    cursor = conn.cursor()

    sections = extract_sections(content)
    compiled = build_compiled_truth(sections)
    timeline = build_timeline(sections)
    title = title or sections[0][1].split("\n")[0][:80] if sections else slug

    now = datetime.utcnow().isoformat()
    summary_json = json.dumps(structured["summary_struct"], ensure_ascii=False)
    concepts_json = json.dumps(structured.get("concepts", []), ensure_ascii=False)

    cursor.execute("""
        INSERT INTO pages (slug, type, title, compiled_truth, timeline, 
                         summary_struct, concepts, decided, learned, completed, next_steps,
                         cause, effect, emotion, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            type=excluded.type, title=excluded.title,
            compiled_truth=excluded.compiled_truth, timeline=excluded.timeline,
            summary_struct=excluded.summary_struct, concepts=excluded.concepts,
            decided=excluded.decided, learned=excluded.learned,
            completed=excluded.completed, next_steps=excluded.next_steps,
            cause=excluded.cause, effect=excluded.effect,
            emotion=excluded.emotion,
            updated_at=excluded.updated_at
    """, (slug, page_type, title, compiled, timeline, 
          summary_json, concepts_json,
          structured["decided"], structured["learned"],
          structured["completed"], structured["next_steps"],
          structured.get("cause", ""), structured.get("effect", ""),
          structured.get("emotion", "无"), now))

    page_id = cursor.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone()[0]

    # Update FTS
    cursor.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    cursor.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                   (page_id, slug, title, content))

    # Update links
    cursor.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        cursor.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))

    # Update tags from concepts
    cursor.execute("DELETE FROM tags WHERE page_id=?", (page_id,))
    for concept in structured.get("concepts", []):
        cursor.execute("INSERT INTO tags (page_id, tag) VALUES (?,?)", (page_id, concept))

    conn.commit()

    # Embed asynchronously
    _embed_page_async(page_id, compiled + "\n\n" + timeline)

    return page_id, structured


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
  init                          Initialize brain.db
  put <slug> [file.md]          Create/update a page (plain)
  put-structured <slug> [file.md] Create/update with AI compression
  compress <text>               AI compress observation (print JSON)
  get <slug>                    Show compiled truth + timeline + structured
  search <query>                FTS5 full-text search
  query <question>              Vector semantic search
  causal <keyword>              因果检索：搜索 cause/effect 字段
  ingest <dir>                  Bulk ingest .md files
  list [--type TYPE]            List pages
  stats                         Show statistics

Environment:
  GBRAIN_DB={GBRAIN_DB}
  SILICONFLOW_API_KEY=<your-key>
  MINIMAX_API_KEY=<for compress>
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
    elif cmd == "compress":
        raw = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip()
        result = compress_observation(raw)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "put-structured":
        if len(sys.argv) < 3:
            print("Usage: gbrain put-structured <slug> [file.md]")
            sys.exit(1)
        slug = sys.argv[2]
        content = open(sys.argv[3]).read() if len(sys.argv) > 3 else sys.stdin.read()
        page_id, structured = put_page_structured(slug, content)
        print(f"Saved: {slug} (id={page_id})")
        print(f"  decided: {structured['decided']}")
        print(f"  learned: {structured['learned']}")
        print(f"  completed: {structured['completed']}")
        print(f"  next_steps: {structured['next_steps']}")
        print(f"  concepts: {structured['concepts']}")
        print(f"  cause: {structured.get('cause', '')}")
        print(f"  effect: {structured.get('effect', '')}")
        print(f"  emotion: {structured.get('emotion', '无')}")
        print(f"  effect: {structured.get('effect', '')}")
    elif cmd == "causal":
        cmd_causal(sys.argv[2] if len(sys.argv) > 2 else "", 20)
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
