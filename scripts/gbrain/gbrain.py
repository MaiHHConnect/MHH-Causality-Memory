#!/usr/bin/env python3
"""
GBrain Python Port — SiliconFlow Qwen3-Embedding-8B
Schema compatible with original gbrain brain.db
Features (v0.16 enhanced):
  - SPlus-inspired: time decay + activation spread
  - MemGPT-inspired: auto-compression of duplicate memories
  - Original: causal reasoning fields (cause/effect) + 13-dim inference
"""

import sqlite3, os, sys, re, hashlib, json, requests, struct
from datetime import datetime
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.expanduser("~/gbrain-data/brain.db"))
SILICONFLOW_API = "https://api.siliconflow.cn/v1"
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
EMBEDDING_DIM = 4096  # Qwen3-Embedding-8B actual output

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
            compiled_truth  TEXT,
            timeline        TEXT,
            summary_struct  TEXT,
            concepts        TEXT,
            decided         TEXT,
            learned         TEXT,
            completed       TEXT,
            next_steps      TEXT,
            cause           TEXT,
            effect          TEXT,
            emotion         TEXT DEFAULT '无',
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS page_fts (
            page_id INTEGER PRIMARY KEY, slug TEXT, title TEXT, body TEXT,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE);
        CREATE VIRTUAL TABLE IF NOT EXISTS page_fts_idx USING fts5(
            slug, title, body, content=page_fts, content_rowid=page_id);
        CREATE TABLE IF NOT EXISTS page_embeddings (
            page_id INTEGER PRIMARY KEY, embedding BLOB,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY, from_page INTEGER, to_slug TEXT,
            FOREIGN KEY (from_page) REFERENCES pages(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY, page_id INTEGER, tag TEXT,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);
        CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_page);
        CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_slug);
        CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
    """)
    try:
        conn.execute("ALTER TABLE pages ADD COLUMN emotion TEXT DEFAULT '无'")
    except Exception:
        pass

# ── Embeddings ──────────────────────────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    if not SILICONFLOW_KEY:
        raise RuntimeError("SILICONFLOW_API_KEY not set")
    resp = requests.post(
        f"{SILICONFLOW_API}/embeddings",
        headers={"Authorization": f"Bearer {SILICONFLOW_KEY}", "Content-Type": "application/json"},
        json={"model": EMBEDDING_MODEL, "input": text}, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x*y for x,y in zip(a,b))
    norm = (sum(x*x for x in a)**0.5) * (sum(x*x for x in b)**0.5)
    return dot/norm if norm else 0.0

def _float32_to_bytes(vec: list[float]) -> bytes:
    return b"".join(struct.pack("f", v) for v in vec)

def _bytes_to_float32(data: bytes) -> list[float]:
    return list(struct.unpack(f"{len(data)//4}f", data))

# ── Markdown parsing ──────────────────────────────────────────────────────────
def extract_sections(content: str) -> list[tuple[str, str]]:
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
    wl = re.findall(r'\[\[([^\]]+)\]\]', content)
    ml = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
    return [l.lower().replace(" ", "-") for l in wl + ml]

def build_compiled_truth(sections: list[tuple[str, str]]) -> str:
    lines = []
    for header, body in sections:
        if header:
            lines.append(f"## {header}")
        first_para = body.split("\n\n")[0].strip()
        if first_para:
            lines.append(first_para)
    return "\n\n".join(lines)

def build_timeline(sections: list[tuple[str, str]]) -> str:
    entries = []
    for header, body in sections:
        meta = f"## {header}" if header else "## (intro)"
        entries.append(meta)
        entries.append(body)
    return "\n\n".join(entries)

# ── SPlus-inspired: Time Decay ────────────────────────────────────────────────
def time_decay(updated_at_str: str, half_life_days: float = 30) -> float:
    """Exponential decay: memory weight halves every `half_life_days` days."""
    try:
        updated = datetime.fromisoformat(updated_at_str)
        days_old = (datetime.now() - updated).total_seconds() / 86400
        return 0.5 ** (days_old / half_life_days)
    except Exception:
        return 0.5  # fallback: neutral weight

# ── SPlus-inspired: Activation Spread ────────────────────────────────────────
def get_activated_pages(page_ids: list[int], top_k: int = 3) -> list[dict]:
    """Given page IDs, spread activation to causally related pages (SPlus deep layer)."""
    conn = get_db()
    activated = []
    for pid in page_ids:
        page = conn.execute("SELECT slug, title FROM pages WHERE id=?", (pid,)).fetchone()
        if not page:
            continue
        # Find pages whose cause/effect mentions this page's slug
        related = conn.execute("""
            SELECT id, slug, title, cause, effect FROM pages
            WHERE id != ? AND (cause LIKE ? OR effect LIKE ? OR slug = ?)
            ORDER BY updated_at DESC LIMIT ?""",
            (pid, f"%{page['slug']}%", f"%{page['slug']}%", page['slug'], top_k)).fetchall()
        for r in related:
            if r['id'] not in page_ids and r['id'] not in [a['id'] for a in activated]:
                activated.append(dict(r))
    return activated

# ── MemGPT-inspired: Auto-Compression ─────────────────────────────────────────
def auto_compress_if_needed(slug: str, title: str):
    """Auto-compress when same slug has >= 3 records (MemGPT tiered memory)."""
    conn = get_db()
    existing = conn.execute("""
        SELECT id, slug, compiled_truth, decided, learned, cause, effect, emotion
        FROM pages WHERE slug=? ORDER BY created_at""", (slug,)).fetchall()
    if len(existing) < 3:
        return  # no compression needed

    context = "\n".join([
        f"记忆{i+1}: {r['compiled_truth'] or r['slug']}"
        for i, r in enumerate(existing)])
    compressed = _llm_compress_context(context, title)
    compressed_json = json.dumps(compressed, ensure_ascii=False)

    conn.execute("""
        UPDATE pages SET type='compressed', summary_struct=?,
        compiled_truth=?, cause=?, effect=?, decided=?, learned=?,
        updated_at=datetime('now') WHERE id=?""",
        (compressed_json, compressed.get('summary', ''),
         compressed.get('cause', ''), compressed.get('effect', ''),
         compressed.get('decided', ''), compressed.get('learned', ''),
         existing[0]['id']))

    ids_to_delete = [r['id'] for r in existing[1:]]
    placeholders = ','.join('?' * len(ids_to_delete))
    conn.execute(f"DELETE FROM pages WHERE id IN ({placeholders})", ids_to_delete)
    conn.commit()
    print(f"[gbrain] auto-compressed {len(existing)} pages → 1 (slug={slug})")

def _llm_compress_context(context: str, title: str) -> dict:
    """Compress multiple memories into one structured summary via LLM."""
    api_key = os.environ.get("MINIMAX_API_KEY", "") or os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        return {"summary": context[:200], "cause": "", "effect": "", "decided": "", "learned": ""}

    prompt = f"""将以下多条关于「{title}」的记忆压缩为一条结构化摘要：

{context}

请用JSON格式输出，包含：
- summary: 整体摘要（50字内）
- cause: 这些记忆的共同前因（20字内）
- effect: 这些记忆的共同后果（20字内）
- decided: 最终决定（20字内）
- learned: 最终学到（20字内）

JSON："""

    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300},
            verify=False,
            timeout=20)
        msg = resp.json().get("choices", [{}])[0].get("message", {})
        text = msg.get("content", "") or msg.get("reasoning_content", "")
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return {"summary": context[:200], "cause": "", "effect": "", "decided": "", "learned": ""}

# ── Core Operations ──────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))

def put_page(slug: str, content: str, page_type: str = "note", title: Optional[str] = None):
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
            updated_at=excluded.updated_at""",
        (slug, page_type, title, compiled, timeline, now))
    page_id = cursor.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone()[0]

    cursor.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    cursor.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                   (page_id, slug, title, content))
    cursor.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        cursor.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))
    conn.commit()
    _embed_page_async(page_id, compiled + "\n\n" + timeline)
    return page_id

def _embed_page_async(page_id: int, text: str):
    try:
        emb = get_embedding(text[:3000])
        conn = get_db()
        cursor = conn.cursor()
        emb_bytes = _float32_to_bytes(emb)
        cursor.execute("DELETE FROM page_embeddings WHERE page_id=?", (page_id,))
        cursor.execute("INSERT INTO page_embeddings (page_id, embedding) VALUES (?,?)",
                       (page_id, emb_bytes))
        conn.commit()
    except Exception as e:
        print(f"[gbrain] embedding failed for page {page_id}: {e}", file=sys.stderr)

# ── Search ───────────────────────────────────────────────────────────────────
def search_fts(query: str, limit: int = 10) -> list[dict]:
    try:
        raw = sqlite3.connect(GBRAIN_DB)
        raw.row_factory = None
        rows = raw.execute(
            "SELECT f.page_id, f.slug, f.title "
            "FROM page_fts f JOIN page_fts_idx idx USING(slug, title) "
            "WHERE page_fts_idx MATCH ? ORDER BY rank LIMIT ?",
            (query, limit)).fetchall()
        raw.close()
        return [{"page_id": r[0], "slug": r[1], "title": r[2]} for r in rows]
    except Exception as e:
        print(f"[gbrain] FTS error: {e}", file=sys.stderr)
        return []

def query_vector(question: str, limit: int = 5) -> list[dict]:
    """Vector semantic search with time decay (SPlus-inspired)."""
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
        emb = _bytes_to_float32(emb_bytes)
        sim = cosine_sim(q_emb, emb)
        page = cursor.execute(
            "SELECT slug, title, updated_at FROM pages WHERE id=?", (page_id,)).fetchone()
        if page:
            decay = time_decay(page["updated_at"])
            results.append({
                "page_id": page_id, "slug": page["slug"], "title": page["title"],
                "score": sim * decay})  # time decay applied
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def search_with_activation(query: str, limit: int = 5) -> list[dict]:
    """FTS + vector search + SPlus activation spread. Returns merged results."""
    fts_results = search_fts(query, limit)
    vec_results = query_vector(query, limit)

    # Deduplicate
    seen = {r['page_id']: r for r in vec_results}
    for r in fts_results:
        pid = r.get('page_id')
        if pid and pid not in seen:
            seen[pid] = {"page_id": pid, "slug": r.get("slug", ""),
                         "title": r.get("title", ""), "score": 0.5}

    results = list(seen.values())
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_results = results[:limit]

    # Activation spread: bring in causally related pages
    activated = get_activated_pages([r['page_id'] for r in top_results], top_k=3)
    for a in activated:
        a['score'] = 0.6  # slightly lower than direct match

    return top_results + activated

# ── Compress (AI) ────────────────────────────────────────────────────────────
def compress_observation(raw_text: str, obs_type: str = "INSIGHT") -> dict:
    """
    AI-powered observation compression (Claude-Mem + 因果推理).
    Returns: {decided, learned, completed, next_steps, concepts, cause, effect, emotion}
    """
    api_key = os.environ.get("MINIMAX_API_KEY", "") or os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        return {"decided": raw_text[:100], "learned": "", "completed": "", "next_steps": "",
                "concepts": [], "cause": "无", "effect": "无", "emotion": "无",
                "summary_struct": {"type": obs_type, "raw": raw_text[:200]}}

    prompt = f"""分析以下观测记录，提取结构化信息。严格按JSON格式回复，不要有其他内容：

观测类型: {obs_type}
内容: {raw_text}

请提取（全部用中文）：
- decided: 决定了什么（核心决策，20字内）
- learned: 学到了什么（关键收获，20字内）
- completed: 完成了什么（已解决/实现，20字内）
- next_steps: 下一步要做什么（待处理事项，20字内）
- concepts: 概念标签（2-4个中文关键词数组）
- cause: 前因——导致这个事件发生的原因（必须推断，15字内，禁止"无"）
- effect: 后果——这个事件会导致什么后续变化（必须推断，15字内，禁止"无"）
- emotion: 当前情绪，从以下选一个：开心|低落|饿|饱|累|精神|焦虑|专注|满足|空虚|无

JSON格式：
{{"decided":"...", "learned":"...", "completed":"...", "next_steps":"...", "concepts":["...","..."], "cause":"...", "effect":"...", "emotion":"..."}}"""

    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500},
            verify=False,
            timeout=30)
        msg = resp.json().get("choices", [{}])[0].get("message", {})
        text = msg.get("content", "") or msg.get("reasoning_content", "")
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            return {
                "decided": data.get("decided", ""),
                "learned": data.get("learned", ""),
                "completed": data.get("completed", ""),
                "next_steps": data.get("next_steps", ""),
                "concepts": data.get("concepts", []) or [],
                "cause": data.get("cause", "") or "无",
                "effect": data.get("effect", "") or "无",
                "emotion": data.get("emotion", "") or "无",
                "summary_struct": {"type": obs_type, "raw": raw_text[:500]}
            }
    except Exception as e:
        print(f"[gbrain] compress failed: {e}", file=sys.stderr)

    return {"decided": raw_text[:100], "learned": "", "completed": "", "next_steps": "",
            "concepts": [], "cause": "无", "effect": "无", "emotion": "无",
            "summary_struct": {"type": obs_type, "raw": raw_text[:200]}}

# ── Structured Put ───────────────────────────────────────────────────────────
def put_page_structured(slug: str, content: str, page_type: str = "note",
                        title: Optional[str] = None, obs_type: str = "INSIGHT"):
    """Create/update with AI compression + MemGPT auto-compress."""
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
            emotion=excluded.emotion, updated_at=excluded.updated_at""",
        (slug, page_type, title, compiled, timeline,
         summary_json, concepts_json,
         structured["decided"], structured["learned"],
         structured["completed"], structured["next_steps"],
         structured.get("cause", ""), structured.get("effect", ""),
         structured.get("emotion", "无"), now))

    page_id = cursor.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone()[0]

    cursor.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    cursor.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                   (page_id, slug, title, content))
    cursor.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        cursor.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))
    cursor.execute("DELETE FROM tags WHERE page_id=?", (page_id,))
    for concept in structured.get("concepts", []):
        cursor.execute("INSERT INTO tags (page_id, tag) VALUES (?,?)", (page_id, concept))
    conn.commit()
    _embed_page_async(page_id, compiled + "\n\n" + timeline)

    # MemGPT-inspired: auto-compress if same slug has >= 3 records
    auto_compress_if_needed(slug, title)

    return page_id, structured

# ── Causal Query ─────────────────────────────────────────────────────────────
def query_causal(keyword: str, limit: int = 10) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT slug, title, cause, effect, decided, learned, emotion
        FROM pages
        WHERE cause LIKE ? OR effect LIKE ?
        ORDER BY updated_at DESC LIMIT ?""",
        (f"%{keyword}%", f"%{keyword}%", limit)).fetchall()
    return [dict(r) for r in rows]

# ── Tag Auto-Extract (SPlus-inspired) ───────────────────────────────────────
def extract_and_set_tags(page_id: int, content: str):
    """Auto-extract tags from content using LLM (SPlus auto-tagging)."""
    api_key = os.environ.get("MINIMAX_API_KEY", "") or os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        return
    prompt = f"从以下内容提取2-4个标签词（只用中文单词，逗号分隔，不需要解释）：\n{content[:300]}"
    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": prompt}], "max_tokens": 80},
            verify=False,
            timeout=10)
        msg = resp.json().get("choices", [{}])[0].get("message", {})
        text = (msg.get("content", "") or msg.get("reasoning_content", "")).strip()
        tags = [t.strip() for t in text.split(',') if t.strip()][:4]
        if tags:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tags WHERE page_id=?", (page_id,))
            for tag in tags:
                cursor.execute("INSERT INTO tags (page_id, tag) VALUES (?,?)", (page_id, tag))
            conn.commit()
            print(f"[gbrain] tags auto-extracted: {tags}")
    except Exception:
        pass

# ── CLI Commands ─────────────────────────────────────────────────────────────
def cmd_init():
    get_db()
    print(f"Initialized: {GBRAIN_DB}")

def cmd_put(slug: str, filepath: Optional[str] = None):
    content = open(filepath).read() if filepath else sys.stdin.read()
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
    """Vector search with time decay + activation spread."""
    all_results = search_with_activation(question, limit)
    activated_slugs = {r['slug'] for r in all_results[limit:]}
    if not all_results:
        print("(no results)")
        return
    for r in all_results:
        tag = " ←因果激活" if r['slug'] in activated_slugs else ""
        print(f"  [{r['slug']}] {r['title']} (score={r['score']:.3f}){tag}")

def cmd_causal(keyword: str, limit: int = 10):
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
        if r.get('decided'):
            print(f"  决定: {r['decided']}")
        if r.get('emotion') and r['emotion'] != '无':
            print(f"  情绪: {r['emotion']}")

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
gbrain.py — GBrain Python Port v0.16 (enhanced)

Commands:
  init                    Initialize brain.db
  put <slug> [file.md]    Create/update page (plain)
  put-structured <slug> [file.md]  Create/update with AI compression
  compress <text>          AI compress observation (print JSON)
  get <slug>              Show compiled truth + timeline + structured
  search <query>          FTS5 full-text search
  query <question>       Vector search + time decay + activation spread
  causal <keyword>        因果检索: search cause/effect fields
  ingest <dir>            Bulk ingest .md files
  list [--type TYPE]      List pages
  stats                   Show statistics

Environment:
  GBRAIN_DB={GBRAIN_DB}
  SILICONFLOW_API_KEY=<for embeddings>
  MINIMAX_API_KEY=<for compress>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE); sys.exit(1)
    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "put":
        if len(sys.argv) < 3:
            print("Usage: gbrain put <slug> [file.md]"); sys.exit(1)
        cmd_put(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
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
            print("Usage: gbrain put-structured <slug> [file.md]"); sys.exit(1)
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
    elif cmd == "causal":
        cmd_causal(sys.argv[2] if len(sys.argv) > 2 else "", 20)
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
