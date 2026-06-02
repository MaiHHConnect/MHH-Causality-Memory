#!/usr/bin/env python3
"""
GBrain Python Port — SiliconFlow Qwen3-Embedding-8B
Schema compatible with original gbrain brain.db
Features (v0.16 enhanced):
  - SPlus-inspired: time decay + activation spread
  - MemGPT-inspired: auto-compression of duplicate memories
  - Original: causal reasoning fields (cause/effect) + 13-dim inference
"""

import sqlite3, os, sys, re, hashlib, json, struct, shutil, time, subprocess
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

# ── Config ──────────────────────────────────────────────────────────────────
GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.expanduser("~/gbrain-data/brain.db"))
LOCAL_EMBED_API = "http://192.168.20.17:8787/embed"
SILICONFLOW_API = "https://api.siliconflow.cn/v1"
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

EMBEDDING_MODEL = "local-gguf"
EMBEDDING_DIM = 768  # local embedding model output dim
SCHEMA_VERSION = 10
CAUSAL_ITEM_TEXT_LIMIT = 200
CAUSAL_SPLIT_RE = re.compile(
    r"[；;。]\s*(?=(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}|\d+[.)、]|因为|由于|导致|所以|结果|前因|后果))"
)

def _clean_causal_text(text: str) -> str:
    """Clean LLM-produced causal text without dropping chain history."""
    value = str(text or "").strip()
    if not value or value == "无":
        return value
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if lines:
        value = "\n".join(re.sub(r"[ \t]+", " ", line) for line in lines)
    else:
        value = re.sub(r"\s+", " ", value)
    return value

def _split_causal_line(line: str) -> list[str]:
    parts = []
    for part in CAUSAL_SPLIT_RE.split(line):
        item = part.strip(" -•\t")
        if item:
            parts.append(item)
    return parts or [line]

def _split_causal_items(text: str, limit: Optional[int] = None) -> list[str]:
    """Split causal text into individual chain items without flattening history."""
    value = _clean_causal_text(text)
    if not value or value == "无":
        return []
    lines = []
    for raw_line in value.splitlines():
        raw_line = raw_line.strip()
        if raw_line:
            lines.extend(_split_causal_line(raw_line))
    if not lines:
        lines = [value]
    out = []
    seen = set()
    for line in lines:
        item = re.sub(r"[ \t]+", " ", line).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item[:CAUSAL_ITEM_TEXT_LIMIT])
        if limit is not None and len(out) >= limit:
            break
    return out

def _merge_causal_text(new_text: str, old_text: str, limit: Optional[int] = None) -> str:
    """Prepend new causal chains while preserving older chains."""
    out = []
    seen = set()
    for item in _split_causal_items(new_text) + _split_causal_items(old_text):
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
        if limit is not None and len(out) >= limit:
            break
    return "\n".join(out)

# ── DB Init ─────────────────────────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(GBRAIN_DB), exist_ok=True)
    conn = sqlite3.connect(GBRAIN_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    if not _schema_current(conn):
        _init_schema(conn)
    return conn

def _schema_current(conn: sqlite3.Connection) -> bool:
    try:
        has_pages = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pages'").fetchone()
        if not has_pages:
            return False
        version = conn.execute("SELECT value FROM config WHERE key='schema_version'").fetchone()
        if not version or str(version[0]) != str(SCHEMA_VERSION):
            return False
        required = {
            "pages": {"raw_event_id", "candidate_id", "evidence", "provenance", "source"},
            "memory_candidates": {"source", "evidence", "provenance", "gate_status", "gate_payload", "gate_reason"},
            "profiles": {"source_refs", "profile_conflicts"},
            "causal_beliefs": {"subject", "predicate", "value", "status", "supersedes", "superseded_by"},
            "belief_candidates": {"subject", "predicate", "value", "belief_type", "candidate_status", "evidence", "evidence_count", "rejection_reason"},
            "causal_events": {"event_time", "actor", "event", "cause", "effect", "evidence"},
            "state_transitions": {"subject", "state_key", "before_value", "after_value", "trigger"},
        }
        for table, columns in required.items():
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if not columns.issubset(existing):
                return False
        return True
    except sqlite3.Error:
        return False

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
        CREATE TABLE IF NOT EXISTS causal_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_page INTEGER NOT NULL,
            to_page INTEGER,
            to_slug TEXT,
            relation_type TEXT DEFAULT 'explains',
            strength TEXT DEFAULT 'weak',
            confidence REAL DEFAULT 0.5,
            evidence TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (from_page) REFERENCES pages(id) ON DELETE CASCADE,
            FOREIGN KEY (to_page) REFERENCES pages(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS raw_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT DEFAULT 'unknown',
            content TEXT NOT NULL,
            source TEXT DEFAULT 'manual',
            metadata TEXT,
            status TEXT DEFAULT 'raw',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS memory_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_event_id INTEGER,
            candidate_type TEXT DEFAULT 'INSIGHT',
            content TEXT NOT NULL,
            cause TEXT,
            effect TEXT,
            decided TEXT,
            learned TEXT,
            next_steps TEXT,
            priority INTEGER DEFAULT 50,
            quality_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'candidate',
            committed_page INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (raw_event_id) REFERENCES raw_events(id) ON DELETE SET NULL,
            FOREIGN KEY (committed_page) REFERENCES pages(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT,
            summary TEXT,
            project_id TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS page_scenes (
            page_id INTEGER NOT NULL,
            scene_id INTEGER NOT NULL,
            PRIMARY KEY (page_id, scene_id),
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
            FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_type TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            evidence TEXT,
            confidence REAL DEFAULT 0.6,
            status TEXT DEFAULT 'active',
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(profile_type, key)
        );
        CREATE TABLE IF NOT EXISTS causal_beliefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            value TEXT NOT NULL,
            belief_type TEXT DEFAULT 'state',
            scope TEXT DEFAULT 'global',
            status TEXT DEFAULT 'active',
            confidence REAL DEFAULT 0.6,
            valid_from TEXT,
            valid_until TEXT,
            evidence TEXT,
            source_slug TEXT,
            source_refs TEXT,
            supersedes TEXT,
            superseded_by INTEGER,
            contradiction TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS belief_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            value TEXT NOT NULL,
            belief_type TEXT NOT NULL,
            scope TEXT DEFAULT 'global',
            candidate_status TEXT DEFAULT 'pending',
            confidence REAL DEFAULT 0.4,
            evidence TEXT NOT NULL,
            reason TEXT,
            evidence_count INTEGER DEFAULT 1,
            rejection_reason TEXT,
            source_slug TEXT,
            source_refs TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS causal_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT,
            actor TEXT NOT NULL,
            event TEXT NOT NULL,
            cause TEXT,
            effect TEXT,
            context TEXT,
            evidence TEXT NOT NULL,
            relation_type TEXT DEFAULT 'causal',
            strength TEXT DEFAULT 'weak',
            confidence REAL DEFAULT 0.6,
            source_slug TEXT,
            source_refs TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS state_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            state_key TEXT NOT NULL,
            before_value TEXT,
            after_value TEXT NOT NULL,
            trigger TEXT,
            reason TEXT,
            evidence TEXT,
            source_slug TEXT,
            event_time TEXT,
            confidence REAL DEFAULT 0.6,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_page);
        CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_slug);
        CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
        CREATE INDEX IF NOT EXISTS idx_causal_edges_from ON causal_edges(from_page);
        CREATE INDEX IF NOT EXISTS idx_causal_edges_to_page ON causal_edges(to_page);
        CREATE INDEX IF NOT EXISTS idx_causal_edges_to_slug ON causal_edges(to_slug);
        CREATE INDEX IF NOT EXISTS idx_causal_edges_relation ON causal_edges(relation_type);
        CREATE INDEX IF NOT EXISTS idx_raw_events_session ON raw_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_raw_events_status ON raw_events(status);
        CREATE INDEX IF NOT EXISTS idx_candidates_status ON memory_candidates(status);
        CREATE INDEX IF NOT EXISTS idx_scenes_slug ON scenes(slug);
        CREATE INDEX IF NOT EXISTS idx_profiles_type ON profiles(profile_type);
        CREATE INDEX IF NOT EXISTS idx_causal_beliefs_lookup ON causal_beliefs(subject, predicate, scope, status);
        CREATE INDEX IF NOT EXISTS idx_causal_beliefs_source ON causal_beliefs(source_slug);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_causal_beliefs_unique_evidence ON causal_beliefs(source_slug, subject, predicate, value);
        CREATE INDEX IF NOT EXISTS idx_belief_candidates_lookup ON belief_candidates(subject, predicate, scope, candidate_status);
        CREATE INDEX IF NOT EXISTS idx_belief_candidates_source ON belief_candidates(source_slug);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_belief_candidates_unique_evidence ON belief_candidates(source_slug, subject, predicate, value);
        CREATE INDEX IF NOT EXISTS idx_causal_events_lookup ON causal_events(actor, event_time, source_slug);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_causal_events_unique_evidence ON causal_events(source_slug, actor, event, evidence);
        CREATE INDEX IF NOT EXISTS idx_state_transitions_lookup ON state_transitions(subject, state_key, event_time);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_state_transitions_unique_evidence ON state_transitions(source_slug, subject, state_key, after_value, event_time);
    """)
    _ensure_column(conn, "pages", "emotion", "TEXT DEFAULT '无'")
    _ensure_column(conn, "pages", "status", "TEXT DEFAULT 'active'")
    _ensure_column(conn, "pages", "supersedes", "TEXT")
    _ensure_column(conn, "pages", "superseded_by", "INTEGER")
    _ensure_column(conn, "pages", "confidence", "REAL DEFAULT 1.0")
    _ensure_column(conn, "pages", "valid_from", "TEXT")
    _ensure_column(conn, "pages", "valid_until", "TEXT")
    _ensure_column(conn, "pages", "user_id", "TEXT DEFAULT 'haoge'")
    _ensure_column(conn, "pages", "agent_id", "TEXT")
    _ensure_column(conn, "pages", "session_id", "TEXT")
    _ensure_column(conn, "pages", "project_id", "TEXT")
    _ensure_column(conn, "pages", "source", "TEXT DEFAULT 'gbrain'")
    _ensure_column(conn, "pages", "visibility", "TEXT DEFAULT 'private'")
    _ensure_column(conn, "pages", "scene_id", "INTEGER")
    _ensure_column(conn, "pages", "raw_event_id", "INTEGER")
    _ensure_column(conn, "pages", "candidate_id", "INTEGER")
    _ensure_column(conn, "pages", "evidence", "TEXT")
    _ensure_column(conn, "pages", "provenance", "TEXT")
    _ensure_column(conn, "memory_candidates", "source", "TEXT")
    _ensure_column(conn, "memory_candidates", "evidence", "TEXT")
    _ensure_column(conn, "memory_candidates", "provenance", "TEXT")
    _ensure_column(conn, "memory_candidates", "gate_status", "TEXT DEFAULT 'ungated'")
    _ensure_column(conn, "memory_candidates", "gate_payload", "TEXT")
    _ensure_column(conn, "memory_candidates", "gate_reason", "TEXT")
    _ensure_column(conn, "profiles", "source_refs", "TEXT")
    _ensure_column(conn, "profiles", "profile_conflicts", "TEXT")
    _ensure_column(conn, "causal_beliefs", "supersedes", "TEXT")
    _ensure_column(conn, "causal_beliefs", "superseded_by", "INTEGER")
    _ensure_column(conn, "belief_candidates", "reason", "TEXT")
    _ensure_column(conn, "belief_candidates", "source_refs", "TEXT")
    _ensure_column(conn, "belief_candidates", "evidence_count", "INTEGER DEFAULT 1")
    _ensure_column(conn, "belief_candidates", "rejection_reason", "TEXT")
    _ensure_column(conn, "causal_events", "context", "TEXT")
    _ensure_column(conn, "causal_events", "relation_type", "TEXT DEFAULT 'causal'")
    _ensure_column(conn, "causal_events", "strength", "TEXT DEFAULT 'weak'")
    _ensure_column(conn, "causal_events", "source_refs", "TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_raw_event ON memory_candidates(raw_event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_raw_event ON pages(raw_event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_candidate ON pages(candidate_id)")
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
    conn.commit()

def _ensure_column(conn: sqlite3.Connection, table: str, column: str, spec: str):
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")

# ── Embeddings ──────────────────────────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    if requests is None:
        raise RuntimeError("requests package not installed; embedding API unavailable")
    # Try local embedding service first
    try:
        resp = requests.post(
            LOCAL_EMBED_API,
            headers={"Content-Type": "application/json"},
            json={"input": text[:3000]}, timeout=30)
        resp.raise_for_status()
        return resp.json()["data"][0]
    except Exception as e:
        pass
    # Fallback to SiliconFlow
    if not SILICONFLOW_KEY:
        raise RuntimeError("Local embedding failed and SILICONFLOW_API_KEY not set")
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

def _infer_event_time(slug: str, title: str, text: str) -> str:
    for value in (slug, title, text):
        match = re.search(r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}", str(value or ""))
        if match:
            return match.group(0).replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
    return ""

def _infer_actor(text: str) -> str:
    value = str(text or "")
    if any(token in value for token in ("浩哥", "用户", "你要求", "你说", "你希望")):
        return "浩哥"
    if any(token in value for token in ("OpenClaw", "openclaw", "系统", "cron", "任务")):
        return "OpenClaw"
    return "待核实"

def _fallback_causal_events_from_sections(slug: str, title: str, sections: list[tuple[str, str]], limit: int = 12) -> list[dict]:
    events = []
    seen = set()
    for header, body in sections:
        text = f"{header}\n{body}".strip()
        if not text:
            continue
        heading = header or title or slug
        event = re.sub(r"^\d{1,2}:\d{2}\s*[—-]\s*", "", heading).strip() or heading
        bullets = [line.strip(" -\t") for line in body.splitlines() if line.strip().startswith(("-", "*"))]
        cause = next((line for line in bullets if any(k in line for k in ("原因", "因为", "由于", "根因", "触发"))), "")
        effect = next((line for line in bullets if any(k in line for k in ("结果", "完成", "已", "导致", "修复", "解决"))), "")
        evidence = " ".join((bullets[:2] or [body.splitlines()[0] if body.splitlines() else event]))[:1000]
        key = (event, evidence)
        if key in seen:
            continue
        seen.add(key)
        events.append({
            "time": _infer_event_time(slug, title, text),
            "actor": _infer_actor(text),
            "event": event[:500],
            "cause": cause[:1000],
            "effect": effect[:1000],
            "context": heading[:1000],
            "evidence": evidence,
            "relation_type": "context" if not cause and not effect else "causal",
            "strength": "unknown" if not cause or not effect else "weak",
            "confidence": 0.45,
        })
        if len(events) >= limit:
            break
    return events

# ── SPlus-inspired: Time Decay ────────────────────────────────────────────────
def time_decay(updated_at_str: str, half_life_days: float = 30) -> float:
    """Exponential decay: memory weight halves every `half_life_days` days."""
    try:
        updated = datetime.fromisoformat(updated_at_str)
        days_old = (datetime.now() - updated).total_seconds() / 86400
        return 0.5 ** (days_old / half_life_days)
    except Exception:
        return 0.5  # fallback: neutral weight

def _page_text(row) -> str:
    return "\n".join(str(row.get(k) or "") if isinstance(row, dict) else str(row[k] or "")
                     for k in ("slug", "title", "compiled_truth", "decided", "learned", "cause", "effect"))

def _active_clause(alias: str = "pages") -> str:
    return f"COALESCE({alias}.status, 'active') = 'active'"

def _embedding_dim(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT embedding FROM page_embeddings LIMIT 1").fetchone()
    return len(row[0]) // 4 if row and row[0] else 0

def _rrf(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)

def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower()))

def _jaccard(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

def _query_terms(text: str, limit: int = 8) -> list[str]:
    value = str(text or "").lower()
    terms = [t for t in re.findall(r"[a-z0-9_][a-z0-9_-]+", value) if len(t) >= 2]
    cjk_runs = re.findall(r"[\u4e00-\u9fff]{2,}", value)
    for run in cjk_runs:
        terms.extend(run[i:i + 2] for i in range(max(0, len(run) - 1)))
    out = []
    seen = set()
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        out.append(term)
        if len(out) >= limit:
            break
    return out

def search_lexical_terms(query: str, limit: int = 20) -> list[dict]:
    terms = [t for t in re.findall(r"[a-z0-9][a-z0-9_-]+", query.lower()) if len(t) >= 2]
    if not terms:
        return []
    conn = get_db()
    where = " OR ".join(["lower(slug || ' ' || title || ' ' || compiled_truth) LIKE ?" for _ in terms])
    rows = conn.execute(f"""
        SELECT id AS page_id, slug, title, compiled_truth AS snippet, updated_at
        FROM pages
        WHERE {_active_clause('pages')} AND ({where})
        ORDER BY updated_at DESC LIMIT ?""", [f"%{t}%" for t in terms] + [limit * 5]).fetchall()
    conn.close()
    ranked = []
    for row in rows:
        text = " ".join(str(row[k] or "") for k in ("slug", "title", "snippet")).lower()
        hits = sum(1 for t in terms if t in text)
        if hits:
            item = dict(row)
            item["lex_hits"] = hits
            ranked.append(item)
    ranked.sort(key=lambda r: (r["lex_hits"], 1 if any(t in str(r.get("slug", "")).lower() for t in terms) else 0), reverse=True)
    return ranked[:limit]

def _lexical_boost(query: str, item: dict) -> float:
    """Small deterministic boost for exact lexical fit; keeps RRF as the base ranker."""
    q = " ".join(query.lower().split())
    slug = str(item.get("slug", "") or "").lower()
    title = str(item.get("title", "") or "").lower()
    snippet = str(item.get("snippet", "") or "").lower()
    text = " ".join((slug, title, snippet))
    if not q or not text:
        return 0.0
    boost = 0.0
    if q in text:
        boost += 0.08
    alnum_terms = [t for t in re.findall(r"[a-z0-9][a-z0-9_-]+", q) if len(t) >= 2]
    for term in alnum_terms:
        if term in slug or term in title:
            boost += 0.03
        elif term in snippet:
            boost += 0.015
    boost = min(boost, 0.12)
    terms = [t for t in re.split(r"\s+", q) if len(t) >= 2]
    if terms:
        hits = sum(1 for term in terms if term in text)
        boost += min(0.06, 0.02 * hits)
    # Chinese queries often have no spaces; reward longer character overlap lightly.
    cjk = [ch for ch in q if "\u4e00" <= ch <= "\u9fff"]
    if cjk:
        overlap = sum(1 for ch in set(cjk) if ch in text)
        cjk_cap = 0.08 if not alnum_terms else 0.06
        boost += min(cjk_cap, overlap / max(len(set(cjk)), 1) * cjk_cap)
    if alnum_terms and re.fullmatch(r"(?:memory-)?\d{4}-\d{2}-\d{2}(?:-md)?", slug):
        title_hits = sum(1 for term in alnum_terms if term in title or term in slug)
        if title_hits == 0:
            boost -= 0.05
    return boost

def _mmr(results: list[dict], limit: int, similarity_threshold: float = 0.82) -> list[dict]:
    selected = []
    for item in sorted(results, key=lambda x: x.get("score", 0), reverse=True):
        text = " ".join(str(item.get(k, "")) for k in ("slug", "title", "snippet"))
        if all(_jaccard(text, " ".join(str(s.get(k, "")) for k in ("slug", "title", "snippet"))) < similarity_threshold for s in selected):
            selected.append(item)
        if len(selected) >= limit:
            break
    return selected

def _quality_score(text: str) -> float:
    if not text or len(text.strip()) < 12:
        return 0.0
    score = 0.2
    long_term_markers = ["决定", "确认", "以后", "长期", "规则", "方案", "修复", "升级", "完成", "问题", "原因", "因为", "所以", "导致", "因此", "需要", "承担", "主记忆", "CausaMem", "记住"]
    score += min(0.5, sum(0.08 for marker in long_term_markers if marker in text))
    if len(text) > 80:
        score += 0.15
    if len(text) > 220:
        score += 0.1
    return min(score, 1.0)

def _candidate_type(text: str) -> str:
    if any(k in text for k in ("决定", "确认", "规则", "以后")):
        return "DECISION"
    if any(k in text for k in ("修复", "bug", "报错", "问题")):
        return "BUG"
    if any(k in text for k in ("完成", "实现", "升级", "改造")):
        return "CHANGE"
    return "INSIGHT"

def _extract_simple_causality(text: str) -> tuple[str, str]:
    cause = ""
    effect = ""
    cause_match = re.search(r"(?:因为|由于|原因是|前因[:：])([^。；\n]+)", text)
    effect_match = re.search(r"(?:所以|导致|后果是|结果是|后果[:：])([^。；\n]+)", text)
    if cause_match:
        cause = cause_match.group(1).strip()[:120]
    if effect_match:
        effect = effect_match.group(1).strip()[:120]
    return cause, effect

def _make_unique_slug(base: str, conn: Optional[sqlite3.Connection] = None) -> str:
    own_conn = conn is None
    conn = conn or get_db()
    slug = slugify(base)[:80] or f"memory-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    candidate = slug
    i = 2
    while conn.execute("SELECT 1 FROM pages WHERE slug=?", (candidate,)).fetchone():
        candidate = f"{slug}-{i}"
        i += 1
    if own_conn:
        conn.close()
    return candidate

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
        related = conn.execute(f"""
            SELECT id, slug, title, cause, effect FROM pages
            WHERE id != ? AND {_active_clause('pages')} AND (cause LIKE ? OR effect LIKE ? OR slug = ?)
            ORDER BY updated_at DESC LIMIT ?""",
            (pid, f"%{page['slug']}%", f"%{page['slug']}%", page['slug'], top_k)).fetchall()
        for r in related:
            if r['id'] not in page_ids and r['id'] not in [a['id'] for a in activated]:
                activated.append(dict(r))
        edge_related = conn.execute(f"""
            SELECT p.id, p.slug, p.title, p.cause, p.effect
            FROM causal_edges e
            JOIN pages p ON p.id = COALESCE(e.to_page, e.from_page)
            WHERE {_active_clause('p')} AND p.id != ? AND (e.from_page = ? OR e.to_page = ?)
            ORDER BY e.confidence DESC, e.created_at DESC LIMIT ?""",
            (pid, pid, pid, top_k)).fetchall()
        for r in edge_related:
            if r['id'] not in page_ids and r['id'] not in [a['id'] for a in activated]:
                activated.append(dict(r))
    return activated

def rebuild_causal_edges_for_page(conn: sqlite3.Connection, page_id: int):
    page = conn.execute("SELECT id, slug, summary_struct, cause, effect FROM pages WHERE id=?", (page_id,)).fetchone()
    if not page:
        return
    conn.execute("DELETE FROM causal_edges WHERE from_page=?", (page_id,))
    for causal_item in _normalize_causal_items(page["summary_struct"], page["cause"], page["effect"]):
        relation_type = causal_item["relation"]
        item = causal_item["text"]
        candidates = conn.execute(f"""
            SELECT id, slug FROM pages
            WHERE id != ? AND {_active_clause('pages')} AND LENGTH(slug) > 2
              AND (? LIKE '%' || slug || '%' OR title LIKE ? OR compiled_truth LIKE ?)
            ORDER BY updated_at DESC LIMIT 5""",
            (page_id, item, f"%{item[:40]}%", f"%{item[:40]}%")).fetchall()
        if candidates:
            for target in candidates:
                conn.execute("""
                    INSERT INTO causal_edges (from_page, to_page, to_slug, relation_type, strength, confidence, evidence)
                    VALUES (?, ?, ?, ?, 'weak', 0.65, ?)""",
                    (page_id, target["id"], target["slug"], relation_type, item))
        else:
            synthetic_slug = slugify(item[:80]) or None
            conn.execute("""
                INSERT INTO causal_edges (from_page, to_slug, relation_type, strength, confidence, evidence)
                VALUES (?, ?, ?, 'weak', 0.45, ?)""",
                (page_id, synthetic_slug, relation_type, item))

def rebuild_all_causal_edges():
    conn = get_db()
    ids = [r[0] for r in conn.execute(f"SELECT id FROM pages WHERE {_active_clause('pages')}").fetchall()]
    for page_id in ids:
        rebuild_causal_edges_for_page(conn, page_id)
    conn.commit()
    return len(ids)

def capture_raw_event(content: str, role: str = "unknown", session_id: Optional[str] = None,
                      source: str = "manual", metadata: Optional[dict] = None) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO raw_events (session_id, role, content, source, metadata)
        VALUES (?, ?, ?, ?, ?)""",
        (session_id, role, content, source, json.dumps(metadata or {}, ensure_ascii=False)))
    conn.commit()
    return cur.lastrowid

def _safe_json_loads(value: str) -> dict:
    try:
        data = json.loads(value or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _causal_items_from_fields(cause: str = "", effect: str = "", limit: Optional[int] = None) -> list[dict]:
    items = []
    for relation, text in (("cause", cause), ("effect", effect)):
        for item in _split_causal_items(text, limit=limit):
            items.append({"relation": relation, "text": item})
            if limit is not None and len(items) >= limit:
                return items
    return items

def _normalize_causal_items(summary_struct, cause: str = "", effect: str = "", limit: Optional[int] = None) -> list[dict]:
    payload = _safe_json_loads(summary_struct) if isinstance(summary_struct, str) else (summary_struct if isinstance(summary_struct, dict) else {})
    raw_items = payload.get("causal_items") if isinstance(payload, dict) else None
    out = []
    seen = set()
    if isinstance(raw_items, list):
        for raw in raw_items:
            if isinstance(raw, dict):
                relation = str(raw.get("relation") or raw.get("type") or "").strip().lower()
                text = str(raw.get("text") or raw.get("content") or raw.get("atom") or raw.get("evidence") or "").strip()
            else:
                relation = ""
                text = str(raw or "").strip()
            if relation not in ("cause", "effect"):
                continue
            for item in _split_causal_items(text):
                key = (relation, item)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"relation": relation, "text": item})
                if limit is not None and len(out) >= limit:
                    return out
    if out:
        return out
    return _causal_items_from_fields(cause, effect, limit=limit)

def _as_list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]

USER_BELIEF_TYPES = {
    "user_preference",
    "negative_preference",
    "user_constraint",
    "user_goal",
    "user_style",
    "user_state",
    "user_decision",
}
BELIEF_TYPE_ALIASES = {
    "preference": "user_preference",
    "pref": "user_preference",
    "negative": "negative_preference",
    "dislike": "negative_preference",
    "constraint": "user_constraint",
    "goal": "user_goal",
    "style": "user_style",
    "state": "user_state",
    "decision": "user_decision",
}

def _normalize_user_subject(value: str) -> str:
    subject = str(value or "").strip()
    if not subject or subject.lower() in {"user", "haoge", "浩哥"} or subject in {"用户", "使用者", "浩哥本人"}:
        return "haoge"
    if subject.startswith(("bench:", "agent:", "project:", "external:")) or subject == "simulated_user":
        return subject[:160]
    return f"external:{subject}"[:160]

def _normalize_user_belief_type(value: str) -> str:
    kind = str(value or "user_state").strip().lower().replace("-", "_")
    kind = BELIEF_TYPE_ALIASES.get(kind, kind)
    return kind if kind in USER_BELIEF_TYPES else ""

def _normalize_causal_beliefs(summary_struct) -> list[dict]:
    payload = _safe_json_loads(summary_struct) if isinstance(summary_struct, str) else (summary_struct if isinstance(summary_struct, dict) else {})
    raw_items = payload.get("causal_beliefs") or payload.get("beliefs") if isinstance(payload, dict) else []
    out = []
    seen = set()
    for raw in _as_list(raw_items):
        if isinstance(raw, str):
            subject, predicate, value = "haoge", "state", raw.strip()
            item = {"belief_type": "user_state"}
        elif isinstance(raw, dict):
            item = raw
            subject = _normalize_user_subject(item.get("subject") or item.get("entity") or "haoge")
            predicate = str(item.get("predicate") or item.get("key") or item.get("state_key") or "state").strip()
            value = str(item.get("value") or item.get("belief") or item.get("after_value") or item.get("text") or "").strip()
        else:
            continue
        if not subject or not predicate or not value:
            continue
        belief_type = _normalize_user_belief_type(item.get("belief_type") or item.get("type") or "user_state")
        if not belief_type:
            continue
        key = (subject.lower(), predicate.lower(), value.lower(), belief_type)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "subject": subject[:160],
            "predicate": predicate[:120],
            "value": value[:500],
            "belief_type": belief_type,
            "scope": str(item.get("scope") or "global")[:120],
            "status": str(item.get("status") or "active")[:40],
            "confidence": float(item.get("confidence") if item.get("confidence") is not None else 0.6),
            "valid_from": str(item.get("valid_from") or item.get("date") or "")[:80],
            "valid_until": str(item.get("valid_until") or "")[:80],
            "evidence": str(item.get("evidence") or item.get("reason") or value)[:1000],
            "source_refs": json.dumps(item.get("source_refs") or [], ensure_ascii=False),
            "supersedes": json.dumps(_as_list(item.get("supersedes")), ensure_ascii=False),
            "contradiction": str(item.get("contradiction") or "")[:1000],
        })
    return out

def _normalize_belief_candidates(summary_struct) -> list[dict]:
    payload = _safe_json_loads(summary_struct) if isinstance(summary_struct, str) else (summary_struct if isinstance(summary_struct, dict) else {})
    if not isinstance(payload, dict):
        return []
    raw_items = payload.get("belief_candidates") or payload.get("user_belief_candidates") or []
    out = []
    seen = set()
    for raw in _as_list(raw_items):
        if not isinstance(raw, dict):
            continue
        subject = _normalize_user_subject(raw.get("subject") or raw.get("entity") or "haoge")
        predicate = str(raw.get("predicate") or raw.get("key") or raw.get("state_key") or "state").strip()
        value = str(raw.get("value") or raw.get("belief") or raw.get("after_value") or raw.get("text") or "").strip()
        evidence = str(raw.get("evidence") or "").strip()
        belief_type = _normalize_user_belief_type(raw.get("belief_type") or raw.get("type") or "")
        if not subject or not predicate or not value or not evidence or not belief_type:
            continue
        status = str(raw.get("candidate_status") or raw.get("status") or "pending").strip().lower()
        if status not in {"pending", "accepted", "rejected"}:
            status = "pending"
        key = (subject.lower(), predicate.lower(), value.lower(), belief_type)
        if key in seen:
            continue
        seen.add(key)
        raw_confidence = float(raw.get("confidence") if raw.get("confidence") is not None else 0.4)
        if status == "pending":
            raw_confidence = min(raw_confidence, 0.6)
        out.append({
            "subject": subject[:160],
            "predicate": predicate[:120],
            "value": value[:500],
            "belief_type": belief_type,
            "scope": str(raw.get("scope") or "global")[:120],
            "candidate_status": status,
            "confidence": raw_confidence,
            "evidence": evidence[:1000],
            "reason": str(raw.get("reason") or "")[:1000],
            "evidence_count": max(1, int(raw.get("evidence_count") or 1)),
            "rejection_reason": str(raw.get("rejection_reason") or "")[:1000],
            "source_refs": json.dumps(raw.get("source_refs") or [], ensure_ascii=False),
        })
    return out

def _normalize_causal_events(summary_struct) -> list[dict]:
    payload = _safe_json_loads(summary_struct) if isinstance(summary_struct, str) else (summary_struct if isinstance(summary_struct, dict) else {})
    if not isinstance(payload, dict):
        return []
    raw_items = payload.get("causal_events") or payload.get("events") or []
    out = []
    seen = set()
    for raw in _as_list(raw_items):
        if not isinstance(raw, dict):
            continue
        actor = str(raw.get("actor") or raw.get("who") or raw.get("person") or "").strip()
        event = str(raw.get("event") or raw.get("what") or raw.get("action") or "").strip()
        evidence = str(raw.get("evidence") or raw.get("quote") or event).strip()
        if not actor or not event or not evidence:
            continue
        relation_type = str(raw.get("relation_type") or "causal").strip().lower()
        if relation_type not in {"causal", "correlation", "conditional", "context"}:
            relation_type = "causal"
        strength = str(raw.get("strength") or "weak").strip().lower()
        if strength not in {"strong", "weak", "unknown"}:
            strength = "weak"
        key = (actor.lower(), event.lower(), evidence.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "event_time": str(raw.get("time") or raw.get("event_time") or raw.get("date") or "")[:80],
            "actor": actor[:160],
            "event": event[:500],
            "cause": str(raw.get("cause") or raw.get("why") or "")[:1000],
            "effect": str(raw.get("effect") or raw.get("result") or "")[:1000],
            "context": str(raw.get("context") or "")[:1000],
            "evidence": evidence[:1000],
            "relation_type": relation_type,
            "strength": strength,
            "confidence": float(raw.get("confidence") if raw.get("confidence") is not None else 0.6),
            "source_refs": json.dumps(raw.get("source_refs") or [], ensure_ascii=False),
        })
    return out

def _normalize_state_transitions(summary_struct) -> list[dict]:
    payload = _safe_json_loads(summary_struct) if isinstance(summary_struct, str) else (summary_struct if isinstance(summary_struct, dict) else {})
    raw_items = payload.get("state_transitions") or payload.get("transitions") if isinstance(payload, dict) else []
    out = []
    seen = set()
    for raw in _as_list(raw_items):
        if not isinstance(raw, dict):
            continue
        subject = _normalize_user_subject(raw.get("subject") or raw.get("entity") or "haoge")
        state_key = str(raw.get("state_key") or raw.get("predicate") or raw.get("key") or "state").strip()
        after_value = str(raw.get("after_value") or raw.get("after") or raw.get("value") or "").strip()
        if not subject or not state_key or not after_value:
            continue
        event_time = str(raw.get("event_time") or raw.get("date") or raw.get("valid_from") or "")[:80]
        key = (subject.lower(), state_key.lower(), after_value.lower(), event_time)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "subject": subject[:160],
            "state_key": state_key[:120],
            "before_value": str(raw.get("before_value") or raw.get("before") or "")[:500],
            "after_value": after_value[:500],
            "trigger": str(raw.get("trigger") or raw.get("event") or "")[:500],
            "reason": str(raw.get("reason") or raw.get("cause") or "")[:1000],
            "evidence": str(raw.get("evidence") or raw.get("trigger") or after_value)[:1000],
            "event_time": event_time,
            "confidence": float(raw.get("confidence") if raw.get("confidence") is not None else 0.6),
        })
    return out

def _sync_causal_cognition(conn: sqlite3.Connection, page_id: int, slug: str, summary_struct: dict):
    events = _normalize_causal_events(summary_struct)
    beliefs = _normalize_causal_beliefs(summary_struct)
    candidates = _normalize_belief_candidates(summary_struct)
    transitions = _normalize_state_transitions(summary_struct)
    conn.execute("DELETE FROM causal_events WHERE source_slug=?", (slug,))
    conn.execute("DELETE FROM causal_beliefs WHERE source_slug=?", (slug,))
    conn.execute("DELETE FROM belief_candidates WHERE source_slug=?", (slug,))
    conn.execute("DELETE FROM state_transitions WHERE source_slug=?", (slug,))
    for event in events:
        conn.execute("""
            INSERT INTO causal_events
                (event_time, actor, event, cause, effect, context, evidence, relation_type, strength, confidence,
                 source_slug, source_refs, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (event["event_time"], event["actor"], event["event"], event["cause"], event["effect"], event["context"],
              event["evidence"], event["relation_type"], event["strength"], event["confidence"], slug, event["source_refs"]))
    for belief in beliefs:
        cur = conn.execute("""
            INSERT INTO causal_beliefs
                (subject, predicate, value, belief_type, scope, status, confidence, valid_from, valid_until,
                 evidence, source_slug, source_refs, supersedes, contradiction, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (belief["subject"], belief["predicate"], belief["value"], belief["belief_type"], belief["scope"],
              belief["status"], belief["confidence"], belief["valid_from"], belief["valid_until"], belief["evidence"],
              slug, belief["source_refs"], belief["supersedes"], belief["contradiction"]))
        if belief["status"] == "active":
            conn.execute("""
                UPDATE causal_beliefs
                SET status='superseded', superseded_by=?, valid_until=COALESCE(NULLIF(?, ''), valid_until), updated_at=datetime('now')
                WHERE id != ? AND status='active' AND subject=? AND predicate=? AND scope=? AND value != ?
                  AND COALESCE(confidence, 0.0) <= ?
            """, (cur.lastrowid, belief["valid_from"], cur.lastrowid, belief["subject"], belief["predicate"], belief["scope"], belief["value"], belief["confidence"]))
    for candidate in candidates:
        existing = conn.execute("""
            SELECT id, confidence, evidence_count, evidence FROM belief_candidates
            WHERE subject=? AND predicate=? AND value=? AND belief_type=? AND scope=?
            ORDER BY updated_at DESC LIMIT 1
        """, (candidate["subject"], candidate["predicate"], candidate["value"], candidate["belief_type"], candidate["scope"])).fetchone()
        if existing and candidate["candidate_status"] == "pending":
            seen_evidence = candidate["evidence"] in (existing["evidence"] or "")
            evidence_count = int(existing["evidence_count"] or 1) + (0 if seen_evidence else candidate["evidence_count"])
            confidence = min(0.85, max(float(existing["confidence"] or 0), candidate["confidence"]) + (0.05 if not seen_evidence else 0.0))
            evidence = existing["evidence"] if seen_evidence else f"{existing['evidence']}\n{candidate['evidence']}"[:1000]
            conn.execute("""
                UPDATE belief_candidates
                SET confidence=?, evidence_count=?, evidence=?, reason=?, source_slug=?, source_refs=?, updated_at=datetime('now')
                WHERE id=?
            """, (confidence, evidence_count, evidence, candidate["reason"], slug, candidate["source_refs"], existing["id"]))
            continue
        conn.execute("""
            INSERT INTO belief_candidates
                (subject, predicate, value, belief_type, scope, candidate_status, confidence, evidence, reason,
                 evidence_count, rejection_reason, source_slug, source_refs, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (candidate["subject"], candidate["predicate"], candidate["value"], candidate["belief_type"], candidate["scope"],
              candidate["candidate_status"], candidate["confidence"], candidate["evidence"], candidate["reason"],
              candidate["evidence_count"], candidate["rejection_reason"], slug, candidate["source_refs"]))
    for transition in transitions:
        conn.execute("""
            INSERT INTO state_transitions
                (subject, state_key, before_value, after_value, trigger, reason, evidence, source_slug, event_time, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (transition["subject"], transition["state_key"], transition["before_value"], transition["after_value"],
              transition["trigger"], transition["reason"], transition["evidence"], slug, transition["event_time"], transition["confidence"]))

def _candidate_provenance(raw_event: Optional[sqlite3.Row] = None, extra: Optional[dict] = None) -> str:
    payload = dict(extra or {})
    if raw_event:
        payload.update({
            "raw_event_id": raw_event["id"],
            "session_id": raw_event["session_id"],
            "role": raw_event["role"],
            "source": raw_event["source"],
            "metadata": _safe_json_loads(raw_event["metadata"]),
        })
    return json.dumps(payload, ensure_ascii=False)

def _candidate_source(row: sqlite3.Row) -> tuple[str, str, str]:
    source = (row["source"] or "").strip() if "source" in row.keys() else ""
    evidence = row["evidence"] or "" if "evidence" in row.keys() else ""
    provenance = row["provenance"] or "{}" if "provenance" in row.keys() else "{}"
    return source or "unknown", evidence, provenance

def extract_candidates(limit: int = 20) -> list[dict]:
    conn = get_db()
    events = conn.execute("""
        SELECT id, session_id, role, content, source, metadata FROM raw_events
        WHERE status='raw' ORDER BY created_at LIMIT ?""", (limit,)).fetchall()
    candidates = []
    for event in events:
        text = event["content"].strip()
        score = _quality_score(text)
        if score >= 0.45:
            cause, effect = _extract_simple_causality(text)
            ctype = _candidate_type(text)
            decided = text[:160] if ctype == "DECISION" else ""
            learned = text[:160] if ctype == "INSIGHT" else ""
            evidence = text[:500]
            provenance = _candidate_provenance(event, {"extractor": "extract_candidates"})
            cur = conn.execute("""
                INSERT INTO memory_candidates
                    (raw_event_id, candidate_type, content, cause, effect, decided, learned, priority, quality_score, source, evidence, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (event["id"], ctype, text, cause, effect, decided, learned, int(score * 100), score, event["source"], evidence, provenance))
            candidates.append({"id": cur.lastrowid, "type": ctype, "score": score, "content": text[:120]})
            conn.execute("UPDATE raw_events SET status='extracted' WHERE id=?", (event["id"],))
        else:
            conn.execute("UPDATE raw_events SET status='ignored' WHERE id=?", (event["id"],))
    conn.commit()
    return candidates

def import_candidates(payload: str) -> list[dict]:
    data = json.loads(payload)
    if isinstance(data, dict):
        items = data.get("memories") or data.get("candidates") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []
    conn = get_db()
    imported = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or item.get("summary") or "").strip()
        if not content:
            continue
        score = float(item.get("quality_score") or item.get("score") or _quality_score(content))
        if score < 0.35:
            continue
        ctype = str(item.get("type") or item.get("candidate_type") or _candidate_type(content)).upper()
        cause = _clean_causal_text(str(item.get("cause") or ""))[:2000]
        effect = _clean_causal_text(str(item.get("effect") or ""))[:2000]
        decided = str(item.get("decided") or (content[:160] if ctype == "DECISION" else ""))[:300]
        learned = str(item.get("learned") or (content[:160] if ctype == "INSIGHT" else ""))[:300]
        next_steps = str(item.get("next_steps") or item.get("next") or "")[:300]
        priority = int(item.get("priority") or min(100, max(1, int(score * 100))))
        raw_event_id = int(item.get("raw_event_id") or 0) or None
        raw_event = None
        if raw_event_id:
            raw_event = conn.execute("SELECT * FROM raw_events WHERE id=?", (raw_event_id,)).fetchone()
            if not raw_event:
                continue
        evidence = str(item.get("evidence") or content[:500]).strip()[:500]
        if raw_event and evidence and evidence not in raw_event["content"]:
            continue
        source = str(item.get("source") or (raw_event["source"] if raw_event else "import")).strip()[:80]
        imported_provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
        provenance = _candidate_provenance(raw_event, {**imported_provenance, "import_source": source})
        cur = conn.execute("""
            INSERT INTO memory_candidates
                (raw_event_id, candidate_type, content, cause, effect, decided, learned, next_steps, priority, quality_score, gate_status, source, evidence, provenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (raw_event_id, ctype, content, cause, effect, decided, learned, next_steps, priority, score, "ungated", source, evidence, provenance))
        imported.append({"id": cur.lastrowid, "type": ctype, "score": score, "content": content[:120]})
    conn.commit()
    return imported

PROFILE_TYPES = {"user", "project", "agent", "preference", "rule"}
PROFILE_KEYS = {
    "memory_system", "execution_tracking", "reasoning_gate", "decision_style", "python_runtime",
    "release_policy", "beads_boundary", "openclaw_integration", "profile_policy",
}
TEMPORARY_MARKERS = ("刚才", "当前", "本次", "这次", "临时", "ready 为空", "返回空", "today", "now", "目前")
UNCERTAIN_MARKERS = ("可能", "大概", "也许", "疑似", "应该", "待核实", "不确定")

def list_gate_candidates(limit: int = 20) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT id, candidate_type, content, cause, effect, decided, learned, next_steps, priority, quality_score, gate_status
        FROM memory_candidates
        WHERE status='candidate' AND COALESCE(gate_status, 'ungated') IN ('ungated', 'pending')
        ORDER BY priority DESC, created_at LIMIT ?""", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(m.lower() in text.lower() for m in markers)

def _normalize_gate_item(item: dict) -> dict:
    candidate_id = int(item.get("candidate_id") or item.get("id") or 0)
    action = str(item.get("action") or item.get("kind") or "reject").lower()
    if action in ("memory", "decision", "rule", "fact"):
        action = "approve"
    if action not in ("approve", "reject", "profile", "scene", "conflict"):
        action = "reject"
    confidence = float(item.get("confidence") or 0)
    evidence = str(item.get("evidence") or "").strip()[:500]
    reason = str(item.get("reason") or "").strip()[:500]
    payload = {
        "candidate_id": candidate_id,
        "action": action,
        "confidence": max(0.0, min(1.0, confidence)),
        "evidence": evidence,
        "reason": reason,
        "scene": item.get("scene") if isinstance(item.get("scene"), dict) else None,
        "profile": item.get("profile") if isinstance(item.get("profile"), dict) else None,
        "stability": str(item.get("stability") or "").lower(),
        "conflicts_with": item.get("conflicts_with") if isinstance(item.get("conflicts_with"), list) else [],
    }
    return payload

def _gate_decision(candidate: sqlite3.Row, decision: dict) -> tuple[str, str, dict]:
    content = str(candidate["content"] or "")
    action = decision["action"]
    confidence = decision["confidence"]
    evidence = decision["evidence"]
    if not evidence:
        return "rejected", "evidence_missing", decision
    if candidate["raw_event_id"]:
        conn = get_db()
        raw = conn.execute("SELECT id, content FROM raw_events WHERE id=?", (candidate["raw_event_id"],)).fetchone()
        conn.close()
        if not raw or evidence not in raw["content"]:
            return "rejected", "evidence_missing_or_not_in_raw_source", decision
        decision["evidence_verified_against"] = "raw_events.content"
        decision["raw_event_id"] = raw["id"]
    elif evidence not in content:
        return "rejected", "evidence_missing_or_not_in_candidate", decision
    else:
        decision["evidence_verified_against"] = "memory_candidates.content"
    if _contains_any(decision.get("reason", "") + " " + decision.get("evidence", ""), UNCERTAIN_MARKERS):
        return "rejected", "uncertain_language", decision
    if action == "profile":
        profile = decision.get("profile") or {}
        ptype = str(profile.get("profile_type") or "").lower()
        key = re.sub(r"[^a-z0-9_]+", "_", str(profile.get("key") or "").lower()).strip("_")
        value = str(profile.get("value") or "").strip()
        if confidence < 0.75:
            return "rejected", "profile_confidence_below_0.75", decision
        if ptype not in PROFILE_TYPES:
            return "rejected", "profile_type_not_allowed", decision
        if key not in PROFILE_KEYS:
            return "rejected", "profile_key_not_allowed", decision
        if not value or len(value) > 240:
            return "rejected", "profile_value_invalid", decision
        if _contains_any(content + " " + value, TEMPORARY_MARKERS) and decision.get("stability") != "long_term":
            return "rejected", "temporary_state_not_profile", decision
        conn = get_db()
        existing = conn.execute("SELECT value, confidence FROM profiles WHERE profile_type=? AND key=? AND status='active'", (ptype, key)).fetchone()
        conn.close()
        if existing and existing["value"] != value and float(existing["confidence"] or 0) >= 0.8:
            return "conflict", "conflicts_with_active_profile", decision
        decision["profile"] = {"profile_type": ptype, "key": key, "value": value}
        return "approved", "profile_gate_passed", decision
    if action == "scene":
        if confidence < 0.55:
            return "rejected", "scene_confidence_below_0.55", decision
        return "approved", "scene_gate_passed", decision
    if action == "approve":
        if confidence < 0.6:
            return "rejected", "memory_confidence_below_0.6", decision
        return "approved", "memory_gate_passed", decision
    if action == "conflict":
        return "conflict", "model_reported_conflict", decision
    return "rejected", "model_rejected", decision

def apply_gate_decisions(payload: str) -> list[dict]:
    data = json.loads(payload)
    items = (data.get("decisions") or data.get("gates") or data.get("items")) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    conn = get_db()
    applied = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        decision = _normalize_gate_item(raw)
        if not decision["candidate_id"]:
            continue
        row = conn.execute("SELECT * FROM memory_candidates WHERE id=?", (decision["candidate_id"],)).fetchone()
        if not row:
            continue
        status, reason, gated = _gate_decision(row, decision)
        conn.execute("""
            UPDATE memory_candidates
            SET gate_status=?, gate_payload=?, gate_reason=?
            WHERE id=?""", (status, json.dumps(gated, ensure_ascii=False), reason, row["id"]))
        applied.append({"candidate_id": row["id"], "gate_status": status, "reason": reason})
    conn.commit()
    conn.close()
    return applied

def apply_gate_payload_to_page(page_slug: str, content: str, gate_payload: Optional[str], candidate_type: str = ""):
    if gate_payload:
        try:
            gate = json.loads(gate_payload)
        except Exception:
            gate = {}
        scene = gate.get("scene") if isinstance(gate, dict) else None
        if isinstance(scene, dict) and scene.get("slug") and scene.get("title"):
            slug = slugify(str(scene["slug"]))
            upsert_scene(slug, str(scene["title"])[:120], str(scene.get("summary") or "")[:500], project_id="causamem")
            attach_scene(slug, page_slug)
        profile = gate.get("profile") if isinstance(gate, dict) else None
        if isinstance(profile, dict) and gate.get("action") == "profile":
            source_refs = gate.get("source_refs") if isinstance(gate.get("source_refs"), list) else []
            if not source_refs and gate.get("raw_event_id"):
                source_refs = [{"type": "raw_event", "id": gate["raw_event_id"]}]
            upsert_profile(
                profile["profile_type"], profile["key"], profile["value"],
                gate.get("evidence", "")[:300], float(gate.get("confidence") or 0.75),
                source_refs=source_refs,
            )
            return
    auto_classify_scene_and_profile(page_slug, content, candidate_type)

def commit_candidates(limit: int = 20, min_score: float = 0.45, approved_only: bool = True) -> list[dict]:
    conn = get_db()
    gate_clause = "COALESCE(gate_status, 'ungated') = 'approved'" if approved_only else "COALESCE(gate_status, 'ungated') IN ('approved', 'ungated')"
    rows = conn.execute(f"""
        SELECT * FROM memory_candidates
        WHERE status='candidate' AND quality_score >= ?
          AND {gate_clause}
        ORDER BY priority DESC, created_at LIMIT ?""", (min_score, limit)).fetchall()
    conn.close()
    committed = []
    for row in rows:
        slug = _make_unique_slug(row["content"][:40])
        content = row["content"]
        page_id, structured = put_page_structured(slug, content, page_type="memory", obs_type=row["candidate_type"])
        conn = get_db()
        source, evidence, provenance = _candidate_source(row)
        gate = _safe_json_loads(row["gate_payload"])
        gate_evidence = str(gate.get("evidence") or evidence or "")[:500]
        page_provenance = _safe_json_loads(provenance)
        page_provenance.update({
            "candidate_id": row["id"],
            "raw_event_id": row["raw_event_id"],
            "gate": gate,
        })
        conn.execute("""
            UPDATE pages SET
                cause=COALESCE(NULLIF(cause, ''), ?),
                effect=COALESCE(NULLIF(effect, ''), ?),
                decided=COALESCE(NULLIF(decided, ''), ?),
                learned=COALESCE(NULLIF(learned, ''), ?),
                next_steps=COALESCE(NULLIF(next_steps, ''), ?),
                raw_event_id=?, candidate_id=?, source=?, session_id=?, evidence=?, provenance=?
            WHERE id=?""",
            (row["cause"], row["effect"], row["decided"], row["learned"], row["next_steps"],
             row["raw_event_id"], row["id"], source, page_provenance.get("session_id"), gate_evidence,
             json.dumps(page_provenance, ensure_ascii=False), page_id))
        rebuild_causal_edges_for_page(conn, page_id)
        conn.execute("""
            UPDATE memory_candidates SET status='committed', committed_page=? WHERE id=?""",
            (page_id, row["id"]))
        conn.commit()
        conn.close()
        apply_gate_payload_to_page(slug, content, row["gate_payload"], row["candidate_type"])
        committed.append({"candidate_id": row["id"], "page_id": page_id, "slug": slug})
    return committed

def infer_scene(content: str, candidate_type: str = "") -> tuple[str, str, str]:
    text = content or ""
    if "CausaMem" in text or "因果记忆" in text or "认知锚定" in text:
        return "causamem-system", "CausaMem 主记忆系统", "CausaMem、因果记忆、认知锚定相关记忆"
    if "Beads" in text or "bd " in text or "beads" in text:
        return "beads-execution-tracking", "Beads 执行追踪", "Beads 任务状态、依赖、审计轨迹相关记忆"
    if "OpenClaw" in text or "插件" in text or "hook" in text:
        return "openclaw-integration", "OpenClaw 集成", "OpenClaw 插件、hook、Agent 运行集成相关记忆"
    if "cron" in text or "定时" in text or "心跳" in text:
        return "automation-cron", "自动化与定时任务", "cron、心跳、自动化任务相关记忆"
    if "DingTalk" in text or "钉钉" in text:
        return "dingtalk-operations", "钉钉运营", "钉钉通道、消息、机器人相关记忆"
    if candidate_type:
        slug = f"candidate-{slugify(candidate_type)}"
        return slug, f"{candidate_type} 候选记忆", f"自动归类的 {candidate_type} 记忆"
    return "general-operations", "通用操作", "未命中特定场景的通用操作记忆"

def auto_classify_scene_and_profile(page_slug: str, content: str, candidate_type: str = ""):
    scene_slug, scene_title, scene_summary = infer_scene(content, candidate_type)
    try:
        upsert_scene(scene_slug, scene_title, scene_summary, project_id="causamem")
        attach_scene(scene_slug, page_slug)
    except Exception as e:
        print(f"[gbrain] scene auto-classify failed for {page_slug}: {e}", file=sys.stderr)
    text = content or ""
    try:
        if "CausaMem" in text and any(k in text for k in ("主记忆", "主系统", "承担")):
            upsert_profile("agent", "memory_system", "CausaMem is the primary memory system", text[:300], 0.9)
        if "Beads" in text or "beads" in text:
            upsert_profile("project", "execution_tracking", "Beads is used as the R0 execution-tracking reality source", text[:300], 0.85)
        if "认知锚定" in text:
            upsert_profile("agent", "reasoning_gate", "Use CausaMem cognitive anchor before judgment", text[:300], 0.85)
        if "浩哥" in text and any(k in text for k in ("偏好", "规则", "确认", "决定")):
            upsert_profile("user", "decision_style", "Prefer factual grounding before conclusions", text[:300], 0.7)
    except Exception as e:
        print(f"[gbrain] profile auto-update failed for {page_slug}: {e}", file=sys.stderr)

def upsert_scene(slug: str, title: str, summary: str = "", project_id: Optional[str] = None) -> int:
    conn = get_db()
    conn.execute("""
        INSERT INTO scenes (slug, title, summary, project_id, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title, summary=excluded.summary, project_id=excluded.project_id,
            updated_at=excluded.updated_at""", (slug, title, summary, project_id))
    conn.commit()
    scene_id = conn.execute("SELECT id FROM scenes WHERE slug=?", (slug,)).fetchone()[0]
    conn.close()
    return scene_id

def attach_scene(scene_slug: str, page_slug: str) -> tuple[int, int]:
    conn = get_db()
    scene = conn.execute("SELECT id FROM scenes WHERE slug=?", (scene_slug,)).fetchone()
    page = conn.execute("SELECT id FROM pages WHERE slug=?", (page_slug,)).fetchone()
    if not scene:
        raise RuntimeError(f"scene not found: {scene_slug}")
    if not page:
        raise RuntimeError(f"page not found: {page_slug}")
    conn.execute("INSERT OR IGNORE INTO page_scenes (page_id, scene_id) VALUES (?, ?)", (page[0], scene[0]))
    conn.execute("UPDATE pages SET scene_id=? WHERE id=?", (scene[0], page[0]))
    conn.commit()
    conn.close()
    return scene[0], page[0]

def upsert_profile(profile_type: str, key: str, value: str, evidence: str = "", confidence: float = 0.6,
                   source_refs: Optional[list[dict]] = None):
    conn = get_db()
    source_refs = source_refs or []
    existing = conn.execute(
        "SELECT value, confidence, profile_conflicts FROM profiles WHERE profile_type=? AND key=? AND status='active'",
        (profile_type, key),
    ).fetchone()
    conflicts = []
    if existing:
        conflicts = _safe_json_loads(existing["profile_conflicts"]).get("items", [])
        if existing["value"] != value:
            conflicts.append({
                "old_value": existing["value"],
                "new_value": value,
                "old_confidence": existing["confidence"],
                "new_confidence": confidence,
                "evidence": evidence,
                "source_refs": source_refs,
                "created_at": datetime.utcnow().isoformat(),
            })
    conn.execute("""
        INSERT INTO profiles (profile_type, key, value, evidence, confidence, source_refs, profile_conflicts, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(profile_type, key) DO UPDATE SET
            value=excluded.value, evidence=excluded.evidence, confidence=excluded.confidence,
            source_refs=excluded.source_refs, profile_conflicts=excluded.profile_conflicts,
            status='active', updated_at=excluded.updated_at""",
        (profile_type, key, value, evidence, confidence,
         json.dumps(source_refs, ensure_ascii=False),
         json.dumps({"items": conflicts}, ensure_ascii=False)))
    conn.commit()
    conn.close()

def trace_memory(keyword: str, depth: int = 2, limit: int = 20) -> list[dict]:
    conn = get_db()
    start = [r[0] for r in conn.execute(f"""
        SELECT id FROM pages WHERE {_active_clause('pages')}
        AND (slug LIKE ? OR title LIKE ? OR compiled_truth LIKE ? OR cause LIKE ? OR effect LIKE ?)
        ORDER BY updated_at DESC LIMIT ?""", [f"%{keyword}%"] * 5 + [limit]).fetchall()]
    seen = set(start)
    frontier = start[:]
    edges = []
    seen_edges = set()
    for _ in range(depth):
        if not frontier:
            break
        placeholders = ','.join('?' * len(frontier))
        rows = conn.execute(f"""
            SELECT e.id, e.from_page, e.relation_type, e.confidence, e.evidence,
                   a.slug AS from_slug, b.slug AS to_slug, e.to_slug AS loose_to_slug,
                   e.to_page
            FROM causal_edges e
            JOIN pages a ON a.id=e.from_page
            LEFT JOIN pages b ON b.id=e.to_page
            WHERE e.from_page IN ({placeholders}) OR e.to_page IN ({placeholders})
            ORDER BY e.confidence DESC, e.created_at DESC
            LIMIT ?""", frontier + frontier + [max(limit * 3, 20)]).fetchall()
        next_frontier = []
        for row in rows:
            if row["id"] in seen_edges:
                continue
            seen_edges.add(row["id"])
            item = dict(row)
            edges.append(item)
            for next_id in (row["from_page"], row["to_page"]):
                if next_id and next_id not in seen:
                    seen.add(next_id)
                    next_frontier.append(next_id)
        frontier = next_frontier
    edges.sort(key=lambda r: (float(r.get("confidence") or 0), str(r.get("evidence") or "")), reverse=True)
    return edges[:limit]

# ── MemGPT-inspired: Auto-Compression ─────────────────────────────────────────
def auto_compress_if_needed(slug: str, title: str):
    """Auto-compress duplicate memories without deleting history."""
    conn = get_db()
    existing = conn.execute("""
        SELECT id, slug, compiled_truth, decided, learned, cause, effect, emotion
        FROM pages WHERE slug=? AND COALESCE(status, 'active') = 'active' ORDER BY created_at""", (slug,)).fetchall()
    if len(existing) < 3:
        return

    context = "\n".join([
        "\n".join([
            f"记忆{i+1}: {r['compiled_truth'] or r['slug']}",
            f"前因: {r['cause'] or ''}",
            f"后果: {r['effect'] or ''}",
        ])
        for i, r in enumerate(existing)])
    compressed = _llm_compress_context(context, title)
    compressed_json = json.dumps(compressed, ensure_ascii=False)

    base_slug = f"{slug}-compressed-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    supersedes = [r['id'] for r in existing]
    conn.execute("""
        INSERT INTO pages (slug, type, title, compiled_truth, summary_struct, cause, effect,
                           decided, learned, supersedes, confidence, updated_at)
        VALUES (?, 'compressed', ?, ?, ?, ?, ?, ?, ?, ?, 0.8, datetime('now'))""",
        (base_slug, title, compressed.get('summary', ''), compressed_json,
         compressed.get('cause', ''), compressed.get('effect', ''),
         compressed.get('decided', ''), compressed.get('learned', ''),
         json.dumps(supersedes, ensure_ascii=False)))
    compressed_id = conn.execute("SELECT id FROM pages WHERE slug=?", (base_slug,)).fetchone()[0]
    placeholders = ','.join('?' * len(supersedes))
    conn.execute(f"UPDATE pages SET status='merged', superseded_by=? WHERE id IN ({placeholders})",
                 [compressed_id] + supersedes)
    conn.commit()
    _embed_page_async(compressed_id, compressed.get('summary', '') + "\n" + context)
    print(f"[gbrain] auto-compressed {len(existing)} pages -> 1, old pages marked merged (slug={slug})")

def _llm_compress_context(context: str, title: str) -> dict:
    """Compress multiple memories into one structured summary via LLM."""
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key or requests is None:
        return {"summary": context[:200], "cause": "", "effect": "", "decided": "", "learned": ""}

    prompt = f"""将以下多条关于「{title}」的记忆压缩为一条结构化摘要：

{context}

请用JSON格式输出，包含：
- summary: 整体摘要（50字内）
- cause: 这些记忆的前因链条（按时间倒序排列；每条包含日期或时间线索；不要添加“最新/较早/更早”等相对标签；尽量保留全部关键链条；每条不超过{CAUSAL_ITEM_TEXT_LIMIT}字；保留必要链条结构）
- effect: 这些记忆的后果链条（按时间倒序排列；每条包含日期或时间线索；不要添加“最新/较早/更早”等相对标签；尽量保留全部关键链条；每条不超过{CAUSAL_ITEM_TEXT_LIMIT}字；保留必要链条结构）
- decided: 最终决定（20字内）
- learned: 最终学到（20字内）

JSON："""

    try:
        resp = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "Qwen/Qwen3-8B", "messages": [{"role": "user", "content": prompt}], "max_tokens": 150},
            timeout=20)
        text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            data["cause"] = _clean_causal_text(data.get("cause", ""))
            data["effect"] = _clean_causal_text(data.get("effect", ""))
            return data
    except Exception:
        pass
    return {"summary": context[:200], "cause": "", "effect": "", "decided": "", "learned": ""}

# ── Core Operations ──────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    slug = re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))
    if slug.strip("-"):
        return slug.strip("-")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"memory-{digest}"

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
    rebuild_causal_edges_for_page(conn, page_id)
    conn.commit()
    _embed_page_async(page_id, compiled + "\n\n" + timeline)
    return page_id

def _embed_page_async(page_id: int, text: str):
    if requests is None:
        return
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
    conn = get_db()
    try:
        rows = conn.execute(f"""
            SELECT page_fts_idx.page_id, page_fts_idx.slug, page_fts_idx.title,
                   snippet(page_fts_idx, 2, '**', '**', '...', 30) AS snippet
            FROM page_fts_idx JOIN pages ON pages.id = page_fts_idx.page_id
            WHERE page_fts_idx MATCH ? AND {_active_clause('pages')}
            ORDER BY rank LIMIT ?""",
            (query, limit)).fetchall()
        return [{**dict(r), "score": 0.0} for r in rows]
    except Exception:
        return []

def search_keyword(query: str, limit: int = 10) -> list[dict]:
    conn = get_db()
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    if not terms:
        return []
    clauses = []
    params = []
    for term in terms:
        like = f"%{term}%"
        clauses.append("(slug LIKE ? OR title LIKE ? OR compiled_truth LIKE ? OR decided LIKE ? OR learned LIKE ? OR cause LIKE ? OR effect LIKE ?)")
        params.extend([like] * 7)
    rows = conn.execute(f"""
        SELECT id AS page_id, slug, title, compiled_truth AS snippet
        FROM pages
        WHERE {_active_clause('pages')} AND ({' OR '.join(clauses)})
        ORDER BY updated_at DESC LIMIT ?""", params + [limit]).fetchall()
    return [dict(r) for r in rows]

def query_vector(question: str, limit: int = 5) -> list[dict]:
    """Vector semantic search with time decay (SPlus-inspired)."""
    try:
        q_emb = get_embedding(question)
    except Exception as e:
        print(f"[gbrain] query embedding failed: {e}", file=sys.stderr)
        return []
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute(f"""
        SELECT e.page_id, e.embedding FROM page_embeddings e
        JOIN pages p ON p.id = e.page_id
        WHERE {_active_clause('p')}""").fetchall()
    results = []
    for page_id, emb_bytes in rows:
        emb = _bytes_to_float32(emb_bytes)
        sim = cosine_sim(q_emb, emb)
        page = cursor.execute(
            "SELECT slug, title, updated_at, confidence FROM pages WHERE id=?", (page_id,)).fetchone()
        if page:
            decay = time_decay(page["updated_at"])
            confidence = page["confidence"] if page["confidence"] is not None else 1.0
            results.append({
                "page_id": page_id, "slug": page["slug"], "title": page["title"],
                "score": sim * decay * confidence})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def search_with_activation(query: str, limit: int = 5) -> list[dict]:
    """RRF(FTS, vector, causal, recency) + MMR + activation spread."""
    fts_results = search_fts(query, limit * 4)
    keyword_results = search_keyword(query, limit * 4)
    lexical_results = search_lexical_terms(query, limit * 4)
    vec_results = query_vector(query, limit * 4)
    conn = get_db()
    causal_rows = conn.execute(f"""
        SELECT DISTINCT p.id AS page_id, p.slug, p.title, e.evidence AS snippet
        FROM causal_edges e JOIN pages p ON p.id = e.from_page
        WHERE {_active_clause('p')} AND (e.evidence LIKE ? OR e.to_slug LIKE ?)
        ORDER BY e.confidence DESC, e.created_at DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit * 4)).fetchall()
    causal_results = [dict(r) for r in causal_rows]
    recency_rows = conn.execute(f"""
        SELECT id AS page_id, slug, title, compiled_truth AS snippet, updated_at, confidence
        FROM pages WHERE {_active_clause('pages')}
        ORDER BY updated_at DESC LIMIT ?""", (limit * 4,)).fetchall()
    recency_results = [dict(r) for r in recency_rows]

    merged: dict[int, dict] = {}
    for source, weight, rows in (("keyword", 1.6, keyword_results), ("lexical", 1.4, lexical_results), ("fts", 1.2, fts_results), ("vector", 1.5, vec_results),
                                 ("causal", 1.1, causal_results), ("recency", 0.4, recency_results)):
        for rank, row in enumerate(rows, start=1):
            pid = row.get("page_id")
            if not pid:
                continue
            item = merged.setdefault(pid, {"page_id": pid, "slug": row.get("slug", ""),
                                            "title": row.get("title", ""), "score": 0.0,
                                            "sources": [], "snippet": row.get("snippet", "")})
            item["score"] += weight * _rrf(rank)
            item["sources"].append(source)
            if row.get("snippet") and not item.get("snippet"):
                item["snippet"] = row.get("snippet")

    for item in merged.values():
        item["score"] += _lexical_boost(query, item)

    top_results = _mmr(list(merged.values()), limit)

    # Activation spread: bring in causally related pages
    activated = get_activated_pages([r['page_id'] for r in top_results], top_k=3)
    for a in activated:
        a['score'] = 0.01
        a['sources'] = ['activation']

    return top_results + activated

# ── Compress (AI) ────────────────────────────────────────────────────────────
def compress_observation(raw_text: str, obs_type: str = "INSIGHT") -> dict:
    """
    AI-powered observation compression (Claude-Mem + 因果推理).
    Returns: {decided, learned, completed, next_steps, concepts, cause, effect, emotion}
    """
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key or requests is None:
        return {"decided": raw_text[:100], "learned": "", "completed": "", "next_steps": "",
                "concepts": [], "cause": "", "effect": "", "emotion": "无",
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
- cause: 前因——导致这个事件发生的原因链条（按时间倒序排列；每条包含日期或时间线索；不要添加“最新/较早/更早”等相对标签；尽量保留全部关键链条；每条不超过{CAUSAL_ITEM_TEXT_LIMIT}字；保留必要链条结构；没有则写"无"）
- effect: 后果——这个事件会导致什么后续变化链条（按时间倒序排列；每条包含日期或时间线索；不要添加“最新/较早/更早”等相对标签；尽量保留全部关键链条；每条不超过{CAUSAL_ITEM_TEXT_LIMIT}字；保留必要链条结构；没有则写"无"）
- emotion: 当前情绪，从以下选一个：开心|低落|饿|饱|累|精神|焦虑|专注|满足|空虚|无
- causal_events: 时人事因果事件数组。这是核心长期记忆：什么时候(time)、什么人(actor)、做了什么(event)、为什么做(cause)、结果是什么(effect)、当时上下文(context)、原文证据(evidence)。只抽有证据的事件；不知道就留空字符串，不要脑补。
- belief_candidates: 用户画像候选数组。只从用户明确原话抽取偏好、负向偏好、约束、目标、风格、状态或决定；不能从行为、话题、任务类型或助手建议推断；证据必须逐字来自用户原句；没把握则返回空数组。

causal_events 每项格式：{{"time":"...", "actor":"...", "event":"...", "cause":"...", "effect":"...", "context":"...", "evidence":"原文证据", "relation_type":"causal|correlation|conditional|context", "strength":"strong|weak|unknown", "confidence":0.6}}
belief_candidates 每项格式：{{"subject":"haoge", "predicate":"...", "value":"...", "belief_type":"user_preference|negative_preference|user_constraint|user_goal|user_style|user_state|user_decision", "scope":"global|current_task", "confidence":0.35, "evidence":"用户原句", "reason":"为什么只是候选"}}
scope规则：出现“这次/现在/当前任务/这轮”用current_task；出现“以后/默认/长期/一直/我喜欢/我不喜欢/我决定”且表达长期意图才用global；不确定则current_task或不抽。

JSON格式：
{{"decided":"...", "learned":"...", "completed":"...", "next_steps":"...", "concepts":["...","..."], "cause":"...", "effect":"...", "emotion":"...", "causal_events":[], "belief_candidates":[]}}"""

    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-M2.7-highspeed", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000},
            timeout=30
        )
        text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        # 去掉 MiniMax 的 think 标签和 markdown 代码块
        def extract_json_from_response(content):
            if not content:
                return None
            # 找最后一个完整的 think 标签之后的内容
            last_think_end = content.rfind('\n</think>')
            if last_think_end != -1:
                result = content[last_think_end+6:].strip()
            else:
                result = content
            # 去掉 markdown 代码块标记
            result = re.sub(r'```json\s*', '', result)
            result = re.sub(r'```\s*$', '', result)
            # 找到第一个 {
            first_brace = result.find('{')
            if first_brace == -1:
                return None
            result = result[first_brace:]
            try:
                return json.loads(result)
            except:
                pass
            # 兜底：找所有 JSON 块，取最后一个
            matches = list(re.finditer(r'\{[^{}]*\}', result))
            if matches:
                for m in reversed(matches):
                    try:
                        return json.loads(m.group())
                    except:
                        continue
            return None

        data = extract_json_from_response(text)
        if data:
            cause = _clean_causal_text(data.get("cause", ""))
            effect = _clean_causal_text(data.get("effect", ""))
            return {
                "decided": data.get("decided", ""),
                "learned": data.get("learned", ""),
                "completed": data.get("completed", ""),
                "next_steps": data.get("next_steps", ""),
                "concepts": data.get("concepts", []),
                "cause": cause,
                "effect": effect,
                "emotion": data.get("emotion", "无"),
                "summary_struct": {
                    "type": obs_type,
                    "raw": raw_text[:500],
                    "causal_items": _causal_items_from_fields(cause, effect),
                    "causal_events": data.get("causal_events", []),
                    "belief_candidates": data.get("belief_candidates", []),
                }
            }
    except Exception as e:
        print(f"[gbrain] compress failed: {e}", file=sys.stderr)

    return {"decided": raw_text[:100], "learned": "", "completed": "", "next_steps": "",
            "concepts": [], "cause": "", "effect": "", "emotion": "无",
            "summary_struct": {"type": obs_type, "raw": raw_text[:200]}}

# ── Structured Put ───────────────────────────────────────────────────────────
def put_page_structured(slug: str, content: str, page_type: str = "note",
                        title: Optional[str] = None, obs_type: str = "INSIGHT",
                        structured_override: Optional[dict] = None,
                        merge_causal: bool = True):
    """Create/update with AI compression + MemGPT auto-compress."""
    structured = structured_override or compress_observation(content, obs_type)
    conn = get_db()
    cursor = conn.cursor()
    sections = extract_sections(content)
    compiled = build_compiled_truth(sections)
    timeline = build_timeline(sections)
    title = title or sections[0][1].split("\n")[0][:80] if sections else slug
    now = datetime.utcnow().isoformat()
    existing = cursor.execute("SELECT cause, effect FROM pages WHERE slug=?", (slug,)).fetchone()
    if existing and merge_causal:
        structured["cause"] = _merge_causal_text(structured.get("cause", ""), existing["cause"])
        structured["effect"] = _merge_causal_text(structured.get("effect", ""), existing["effect"])
    summary_struct = structured.get("summary_struct")
    if not isinstance(summary_struct, dict):
        summary_struct = {"type": obs_type, "raw": content[:500]}
    if not summary_struct.get("causal_events"):
        summary_struct["causal_events"] = _fallback_causal_events_from_sections(slug, title, sections)
    summary_struct["causal_items"] = _normalize_causal_items(
        summary_struct,
        structured.get("cause", ""),
        structured.get("effect", ""),
    )
    structured["summary_struct"] = summary_struct
    summary_json = json.dumps(summary_struct, ensure_ascii=False)
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
    _sync_causal_cognition(conn, page_id, slug, summary_struct)

    cursor.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    cursor.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                   (page_id, slug, title, content))
    cursor.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        cursor.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))
    cursor.execute("DELETE FROM tags WHERE page_id=?", (page_id,))
    for concept in structured.get("concepts", []):
        cursor.execute("INSERT INTO tags (page_id, tag) VALUES (?,?)", (page_id, concept))
    rebuild_causal_edges_for_page(conn, page_id)
    conn.commit()
    _embed_page_async(page_id, compiled + "\n\n" + timeline)

    # MemGPT-inspired: auto-compress if same slug has >= 3 records
    auto_compress_if_needed(slug, title)

    return page_id, structured

# ── Causal Query ─────────────────────────────────────────────────────────────
def query_causal(keyword: str, limit: int = 10) -> list[dict]:
    conn = get_db()
    rows = conn.execute(f"""
        SELECT DISTINCT p.slug, p.title, p.summary_struct, p.cause, p.effect, p.decided, p.learned, p.emotion,
               e.relation_type, e.evidence, e.confidence
        FROM pages p
        LEFT JOIN causal_edges e ON e.from_page = p.id
        WHERE {_active_clause('p')} AND (p.slug LIKE ? OR p.title LIKE ? OR p.compiled_truth LIKE ? OR p.decided LIKE ? OR p.learned LIKE ? OR p.cause LIKE ? OR p.effect LIKE ? OR p.summary_struct LIKE ? OR e.evidence LIKE ? OR e.to_slug LIKE ?)
        ORDER BY COALESCE(e.confidence, 0.0) DESC, p.updated_at DESC LIMIT ?""",
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit)).fetchall()
    results = [dict(r) for r in rows]
    if len(results) < limit:
        seen = {r["slug"] for r in results}
        for term in _query_terms(keyword):
            if len(results) >= limit:
                break
            more = conn.execute(f"""
                SELECT DISTINCT p.slug, p.title, p.summary_struct, p.cause, p.effect, p.decided, p.learned, p.emotion,
                       e.relation_type, e.evidence, e.confidence
                FROM pages p
                LEFT JOIN causal_edges e ON e.from_page = p.id
                WHERE {_active_clause('p')} AND (p.slug LIKE ? OR p.title LIKE ? OR p.compiled_truth LIKE ? OR p.decided LIKE ? OR p.learned LIKE ? OR p.cause LIKE ? OR p.effect LIKE ? OR p.summary_struct LIKE ? OR e.evidence LIKE ? OR e.to_slug LIKE ?)
                ORDER BY COALESCE(e.confidence, 0.0) DESC, p.updated_at DESC LIMIT ?""",
                (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", limit)).fetchall()
            for row in more:
                item = dict(row)
                if item["slug"] in seen:
                    continue
                seen.add(item["slug"])
                results.append(item)
                if len(results) >= limit:
                    break
    results.sort(key=lambda r: (_jaccard(keyword, " ".join(str(r.get(k) or "") for k in ("slug", "title", "cause", "effect", "evidence"))), float(r.get("confidence") or 0)), reverse=True)
    return results[:limit]

def query_causal_beliefs(question: str, limit: int = 8) -> list[dict]:
    conn = get_db()
    terms = _query_terms(question)
    clauses = []
    params = []
    for term in terms[:12]:
        like = f"%{term}%"
        clauses.append("(subject LIKE ? OR predicate LIKE ? OR value LIKE ? OR evidence LIKE ? OR contradiction LIKE ?)")
        params.extend([like] * 5)
    where = f" AND ({' OR '.join(clauses)})" if clauses else ""
    rows = conn.execute(f"""
        SELECT id, subject, predicate, value, belief_type, scope, status, confidence, valid_from, valid_until,
               evidence, source_slug, superseded_by, contradiction, updated_at
        FROM causal_beliefs
        WHERE 1=1{where}
        ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, confidence DESC, COALESCE(NULLIF(valid_from, ''), updated_at) DESC
        LIMIT ?
    """, params + [max(limit * 3, 20)]).fetchall()
    scored = []
    for row in rows:
        item = dict(row)
        text = " ".join(str(item.get(k) or "") for k in ("subject", "predicate", "value", "evidence", "contradiction"))
        score = _jaccard(question, text) + float(item.get("confidence") or 0) * 0.25
        if item.get("status") == "active":
            score += 0.5
        scored.append((score, item))
    conn.close()
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _score, item in scored[:limit]]

def query_belief_candidates(question: str, limit: int = 5) -> list[dict]:
    conn = get_db()
    terms = _query_terms(question)
    clauses = []
    params = []
    for term in terms[:12]:
        like = f"%{term}%"
        clauses.append("(subject LIKE ? OR predicate LIKE ? OR value LIKE ? OR evidence LIKE ? OR reason LIKE ?)")
        params.extend([like] * 5)
    where = f" AND ({' OR '.join(clauses)})" if clauses else ""
    rows = conn.execute(f"""
        SELECT id, subject, predicate, value, belief_type, scope, candidate_status, confidence,
               evidence, reason, evidence_count, rejection_reason, source_slug, updated_at
        FROM belief_candidates
        WHERE candidate_status='pending'{where}
        ORDER BY confidence DESC, updated_at DESC
        LIMIT ?
    """, params + [max(limit * 3, 15)]).fetchall()
    scored = []
    for row in rows:
        item = dict(row)
        text = " ".join(str(item.get(k) or "") for k in ("subject", "predicate", "value", "evidence", "reason"))
        scored.append((_jaccard(question, text) + float(item.get("confidence") or 0) * 0.2 + min(int(item.get("evidence_count") or 1), 5) * 0.03, item))
    conn.close()
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _score, item in scored[:limit]]

def query_causal_events(question: str, limit: int = 10) -> list[dict]:
    conn = get_db()
    terms = _query_terms(question)
    clauses = []
    params = []
    for term in terms[:12]:
        like = f"%{term}%"
        clauses.append("(event_time LIKE ? OR actor LIKE ? OR event LIKE ? OR cause LIKE ? OR effect LIKE ? OR context LIKE ? OR evidence LIKE ?)")
        params.extend([like] * 7)
    where = f" AND ({' OR '.join(clauses)})" if clauses else ""
    rows = conn.execute(f"""
        SELECT id, event_time, actor, event, cause, effect, context, evidence, relation_type, strength,
               confidence, source_slug, updated_at
        FROM causal_events
        WHERE 1=1{where}
        ORDER BY COALESCE(NULLIF(event_time, ''), updated_at) DESC, confidence DESC
        LIMIT ?
    """, params + [max(limit * 3, 30)]).fetchall()
    scored = []
    for row in rows:
        item = dict(row)
        text = " ".join(str(item.get(k) or "") for k in ("event_time", "actor", "event", "cause", "effect", "context", "evidence"))
        scored.append((_jaccard(question, text) + float(item.get("confidence") or 0) * 0.15, item))
    conn.close()
    scored.sort(key=lambda x: (x[0], _line_date_key(x[1].get("event_time") or "")), reverse=True)
    return [item for _score, item in scored[:limit]]

def reject_belief_candidate(candidate_id: int, reason: str, evidence: str = "") -> bool:
    conn = get_db()
    cur = conn.execute("""
        UPDATE belief_candidates
        SET candidate_status='rejected', rejection_reason=?, reason=COALESCE(NULLIF(?, ''), reason), updated_at=datetime('now')
        WHERE id=? AND candidate_status!='rejected'
    """, (reason[:1000], evidence[:1000], candidate_id))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed

def reject_causal_belief(belief_id: int, reason: str, evidence: str = "") -> bool:
    conn = get_db()
    note = reason[:1000]
    if evidence:
        note = f"{note}；纠正证据：{evidence[:500]}"
    cur = conn.execute("""
        UPDATE causal_beliefs
        SET status='rejected', contradiction=?, valid_until=COALESCE(NULLIF(valid_until, ''), datetime('now')), updated_at=datetime('now')
        WHERE id=? AND status!='rejected'
    """, (note, belief_id))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed

def query_state_transitions(question: str, limit: int = 8) -> list[dict]:
    conn = get_db()
    terms = _query_terms(question)
    clauses = []
    params = []
    for term in terms[:12]:
        like = f"%{term}%"
        clauses.append("(subject LIKE ? OR state_key LIKE ? OR before_value LIKE ? OR after_value LIKE ? OR trigger LIKE ? OR reason LIKE ? OR evidence LIKE ?)")
        params.extend([like] * 7)
    where = f" AND ({' OR '.join(clauses)})" if clauses else ""
    rows = conn.execute(f"""
        SELECT subject, state_key, before_value, after_value, trigger, reason, evidence, source_slug, event_time, confidence
        FROM state_transitions
        WHERE 1=1{where}
        ORDER BY COALESCE(NULLIF(event_time, ''), created_at) DESC, confidence DESC
        LIMIT ?
    """, params + [max(limit * 3, 20)]).fetchall()
    scored = []
    for row in rows:
        item = dict(row)
        text = " ".join(str(item.get(k) or "") for k in ("subject", "state_key", "before_value", "after_value", "trigger", "reason", "evidence"))
        scored.append((_jaccard(question, text) + float(item.get("confidence") or 0) * 0.2, item))
    conn.close()
    scored.sort(key=lambda x: (_line_date_key(x[1].get("event_time") or ""), x[0]), reverse=True)
    return [item for _score, item in scored[:limit]]

def _belief_anchor_lines(question: str, limit: int = 8) -> list[str]:
    lines = []
    for item in query_causal_beliefs(question, limit):
        status = "当前" if item.get("status") == "active" else "已被推翻"
        parts = [f"[{item.get('source_slug') or 'belief'}] {status}画像：{item.get('subject')} {item.get('predicate')} = {item.get('value')}"]
        if item.get("valid_from"):
            parts.append(f"生效：{item['valid_from']}")
        if item.get("confidence") is not None:
            parts.append(f"置信度：{float(item.get('confidence') or 0):.2f}")
        if item.get("evidence_count"):
            parts.append(f"证据次数：{int(item.get('evidence_count') or 1)}")
        if item.get("evidence"):
            parts.append(f"证据：{item['evidence']}")
        if item.get("contradiction"):
            parts.append(f"冲突：{item['contradiction']}")
        lines.append("；".join(parts))
    return _unique_lines(lines, limit)

def _causal_event_anchor_lines(question: str, limit: int = 10) -> list[str]:
    lines = []
    for item in query_causal_events(question, limit):
        time_part = item.get("event_time") or "时间待核实"
        actor = item.get("actor") or "人物待核实"
        event = item.get("event") or "事件待核实"
        cause = item.get("cause") or "原因待核实"
        effect = item.get("effect") or "结果待核实"
        line = f"[{item.get('source_slug') or 'event'}] 时：{time_part}；人：{actor}；事：{event}；因：{cause}；果：{effect}"
        extras = []
        if item.get("context"):
            extras.append(f"上下文：{item['context']}")
        if item.get("relation_type") or item.get("strength"):
            extras.append(f"关系：{item.get('relation_type') or 'causal'}/{item.get('strength') or 'weak'}")
        if item.get("evidence"):
            extras.append(f"证据：{item['evidence']}")
        if extras:
            line = f"{line}；" + "；".join(extras)
        lines.append(line)
    return _unique_lines(lines, limit)

def _belief_candidate_anchor_lines(question: str, limit: int = 5) -> list[str]:
    lines = []
    for item in query_belief_candidates(question, limit):
        parts = [f"[{item.get('source_slug') or 'candidate'}] 待确认画像：{item.get('subject')} {item.get('predicate')} = {item.get('value')}"]
        if item.get("confidence") is not None:
            parts.append(f"置信度：{float(item.get('confidence') or 0):.2f}")
        if item.get("evidence"):
            parts.append(f"证据：{item['evidence']}")
        if item.get("reason"):
            parts.append(f"原因：{item['reason']}")
        lines.append("；".join(parts))
    return _unique_lines(lines, limit)

def _transition_anchor_lines(question: str, limit: int = 8) -> list[str]:
    lines = []
    for item in query_state_transitions(question, limit):
        before = item.get("before_value") or "未知"
        after = item.get("after_value") or "未知"
        date = f"{item['event_time']} " if item.get("event_time") else ""
        line = f"[{item.get('source_slug') or 'transition'}] {date}{item.get('subject')} 的用户状态 {item.get('state_key')}：{before} -> {after}"
        extras = []
        if item.get("trigger"):
            extras.append(f"触发：{item['trigger']}")
        if item.get("reason"):
            extras.append(f"原因：{item['reason']}")
        if item.get("evidence"):
            extras.append(f"证据：{item['evidence']}")
        if extras:
            line = f"{line}；" + "；".join(extras)
        lines.append(line)
    return _unique_lines(lines, limit)

# ── Tag Auto-Extract (SPlus-inspired) ───────────────────────────────────────
def extract_and_set_tags(page_id: int, content: str):
    """Auto-extract tags from content using LLM (SPlus auto-tagging)."""
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key or requests is None:
        return
    prompt = f"从以下内容提取2-4个标签词（只用中文单词，逗号分隔，不需要解释）：\n{content[:300]}"
    try:
        resp = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "Qwen/Qwen3-8B", "messages": [{"role": "user", "content": prompt}], "max_tokens": 40},
            timeout=10)
        text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
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
    active = cur.execute("SELECT COUNT(*) FROM pages WHERE COALESCE(status, 'active')='active'").fetchone()[0]
    merged = cur.execute("SELECT COUNT(*) FROM pages WHERE status='merged'").fetchone()[0]
    embeddings = cur.execute("SELECT COUNT(*) FROM page_embeddings").fetchone()[0]
    links = cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    edges = cur.execute("SELECT COUNT(*) FROM causal_edges").fetchone()[0]
    raw_events = cur.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
    candidates = cur.execute("SELECT COUNT(*) FROM memory_candidates").fetchone()[0]
    scenes = cur.execute("SELECT COUNT(*) FROM scenes").fetchone()[0]
    profiles = cur.execute("SELECT COUNT(*) FROM profiles WHERE status='active'").fetchone()[0]
    version = cur.execute("SELECT value FROM config WHERE key='schema_version'").fetchone()
    print(f"pages: {pages}")
    print(f"active_pages: {active}")
    print(f"merged_pages: {merged}")
    print(f"embeddings: {embeddings}")
    print(f"links: {links}")
    print(f"causal_edges: {edges}")
    print(f"raw_events: {raw_events}")
    print(f"memory_candidates: {candidates}")
    print(f"scenes: {scenes}")
    print(f"profiles: {profiles}")
    print(f"schema_version: {version[0] if version else 'unknown'}")

def cmd_doctor():
    conn = get_db()
    issues = []
    dim = _embedding_dim(conn)
    if dim and dim != EMBEDDING_DIM:
        issues.append(f"embedding dim mismatch: db={dim}, expected={EMBEDDING_DIM}")
    missing = conn.execute(f"""
        SELECT COUNT(*) FROM pages p LEFT JOIN page_embeddings e ON e.page_id=p.id
        WHERE {_active_clause('p')} AND e.page_id IS NULL""").fetchone()[0]
    if missing:
        issues.append(f"active pages without embedding: {missing}")
    version = conn.execute("SELECT value FROM config WHERE key='schema_version'").fetchone()
    print(f"db: {GBRAIN_DB}")
    print(f"schema_version: {version[0] if version else 'unknown'}")
    print(f"embedding_dim: {dim or 'none'} expected={EMBEDDING_DIM}")
    if issues:
        print("issues:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    print("doctor: ok")

def cmd_backup():
    get_db().close()
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dst = f"{GBRAIN_DB}.backup.{stamp}"
    shutil.copy2(GBRAIN_DB, dst)
    print(dst)

def cmd_migrate():
    conn = get_db()
    count = rebuild_all_causal_edges()
    print(f"migrated schema={SCHEMA_VERSION}, rebuilt causal edges for {count} pages")

def cmd_eval(eval_path: Optional[str] = None):
    eval_path = eval_path or os.path.expanduser("~/MHH-Causality-Memory/eval/gbrain_eval.jsonl")
    questions = []
    if os.path.exists(eval_path):
        with open(eval_path) as f:
            questions = [json.loads(line) for line in f if line.strip()]
    else:
        questions = [
            {"q": "CausaMem 是不是主系统？", "slugs": ["causamem-main-system-20260530"]},
            {"q": "CausaMem 主系统", "slugs": ["causamem-main-system-20260530"]},
        ]
    total = len(questions)
    hit = 0
    rr_sum = 0.0
    started = time.time()
    for item in questions:
        expected = set(item.get("slugs", []))
        results = search_with_activation(item["q"], 10)
        slugs = [r["slug"] for r in results]
        rank = next((i + 1 for i, slug in enumerate(slugs) if slug in expected), None)
        if rank:
            hit += 1
            rr_sum += 1.0 / rank
        print(json.dumps({"q": item["q"], "expected": list(expected), "top": slugs[:5], "rank": rank}, ensure_ascii=False))
    print(f"hit_rate: {hit / total if total else 0:.3f}")
    print(f"mrr: {rr_sum / total if total else 0:.3f}")
    print(f"elapsed_ms: {int((time.time() - started) * 1000)}")

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

def cmd_capture():
    content = sys.stdin.read().strip() if len(sys.argv) < 3 else sys.argv[2]
    if not content:
        print("Usage: gbrain capture <text>"); sys.exit(1)
    event_id = capture_raw_event(content)
    print(f"captured raw_event: {event_id}")

def cmd_extract():
    candidates = extract_candidates()
    print(f"extracted: {len(candidates)}")
    for c in candidates:
        print(json.dumps(c, ensure_ascii=False))

def cmd_import_candidates():
    payload = sys.stdin.read().strip()
    if not payload:
        print("Usage: gbrain import-candidates < candidates.json"); sys.exit(1)
    imported = import_candidates(payload)
    print(f"imported: {len(imported)}")
    for c in imported:
        print(json.dumps(c, ensure_ascii=False))

def cmd_gate_candidates():
    json_mode = "--json" in sys.argv
    limit = 20
    for arg in sys.argv[2:]:
        if arg.isdigit():
            limit = int(arg)
    rows = list_gate_candidates(limit)
    if json_mode:
        print(json.dumps({"candidates": rows}, ensure_ascii=False, indent=2))
        return
    for row in rows:
        print(f"[{row['id']}] {row['candidate_type']} score={row['quality_score']:.2f} gate={row['gate_status']} {row['content'][:120]}")

def cmd_apply_gates():
    payload = sys.stdin.read().strip()
    if not payload:
        print("Usage: gbrain apply-gates < gates.json"); sys.exit(1)
    applied = apply_gate_decisions(payload)
    print(f"gated: {len(applied)}")
    for item in applied:
        print(json.dumps(item, ensure_ascii=False))

def cmd_commit():
    committed = commit_candidates(approved_only="--allow-ungated" not in sys.argv)
    print(f"committed: {len(committed)}")
    for c in committed:
        print(json.dumps(c, ensure_ascii=False))

def cmd_scene():
    if len(sys.argv) < 4:
        print("Usage: gbrain scene <slug> <title> [summary]"); sys.exit(1)
    scene_id = upsert_scene(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    print(f"scene: {scene_id}")

def cmd_attach_scene():
    if len(sys.argv) < 4:
        print("Usage: gbrain attach-scene <scene-slug> <page-slug>"); sys.exit(1)
    scene_id, page_id = attach_scene(sys.argv[2], sys.argv[3])
    print(f"attached scene={scene_id} page={page_id}")

def cmd_profile():
    if len(sys.argv) < 5:
        print("Usage: gbrain profile <type> <key> <value> [evidence]"); sys.exit(1)
    upsert_profile(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "")
    print(f"profile saved: {sys.argv[2]}.{sys.argv[3]}")

def cmd_profiles():
    conn = get_db()
    rows = conn.execute("""
        SELECT profile_type, key, value, confidence, updated_at FROM profiles
        WHERE status='active' ORDER BY profile_type, key""").fetchall()
    for r in rows:
        print(f"[{r['profile_type']}] {r['key']} = {r['value']} (confidence={r['confidence']:.2f})")

def cmd_auto_classify():
    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 50
    conn = get_db()
    rows = conn.execute("""
        SELECT slug, type, title, compiled_truth, decided, learned, cause, effect
        FROM pages
        WHERE COALESCE(status, 'active')='active'
        ORDER BY updated_at DESC LIMIT ?""", (limit,)).fetchall()
    conn.close()
    count = 0
    for row in rows:
        content = "\n".join(str(row[k] or "") for k in ("title", "compiled_truth", "decided", "learned", "cause", "effect"))
        auto_classify_scene_and_profile(row["slug"], content, row["type"] or "")
        count += 1
    print(f"auto-classified: {count}")

def cmd_trace():
    keyword = sys.argv[2] if len(sys.argv) > 2 else ""
    rows = trace_memory(keyword)
    if not rows:
        print(f"(no trace for: {keyword})")
        return
    for r in rows:
        target = r.get("to_slug") or r.get("loose_to_slug") or "?"
        print(f"{r.get('from_slug')} --{r.get('relation_type')}--> {target} ({r.get('confidence')})")
        if r.get("evidence"):
            print(f"  evidence: {r['evidence']}")

def cmd_why():
    keyword = sys.argv[2] if len(sys.argv) > 2 else ""
    rows = query_causal(keyword, 8)
    if not rows:
        print(f"(no why for: {keyword})")
        return
    for r in rows:
        print(f"[{r['slug']}] {r['title']}")
        reason = r.get("cause") or r.get("evidence") or r.get("decided") or r.get("learned") or "待补因果"
        print(f"  why: {reason}")

def _unique_lines(values: list[str], limit: int = 6) -> list[str]:
    seen = set()
    out = []
    for value in values:
        text = " ".join(str(value or "").split())
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text[:220])
        if len(out) >= limit:
            break
    return out

def _unique_causal_lines(values: list[str], limit: int = 8) -> list[str]:
    seen = set()
    out = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        for item in _split_causal_items(text, limit=limit):
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
            if len(out) >= limit:
                return out
    return out

def _trace_anchor_line(row: dict) -> str:
    relation = row.get("relation_type")
    evidence = row.get("evidence") or "待补"
    from_slug = row.get("from_slug") or "?"
    target = row.get("to_slug") or row.get("loose_to_slug") or "?"
    if relation == "cause":
        return f"{target} --前因--> {from_slug}；证据：{evidence}"
    if relation == "effect":
        return f"{from_slug} --后果--> {target}；证据：{evidence}"
    return f"{from_slug} --{relation or 'related'}--> {target}；证据：{evidence}"

def _rank_causal_anchor_lines(question: str, field_lines: list[str], trace: list[dict], limit: int) -> list[str]:
    candidates = []
    for line in field_lines:
        candidates.append((3.0 + _jaccard(question, line), line))
    for row in trace:
        line = _trace_anchor_line(row)
        confidence = float(row.get("confidence") or 0)
        penalty = -0.2 if row.get("loose_to_slug") and not row.get("to_slug") else 0.0
        candidates.append((1.0 + confidence + _jaccard(question, line) + penalty, line))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return _unique_causal_lines([line for _score, line in candidates], limit)

def _line_date_key(line: str) -> str:
    match = re.search(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", str(line or ""))
    return match.group(0).replace("/", "-") if match else ""

def _anchor_structured_lines(question: str, keys: tuple[str, ...], limit: int = 8) -> list[str]:
    conn = get_db()
    terms = _query_terms(question)
    terms = list(dict.fromkeys([t.lower() for t in terms if t]))
    clauses = []
    params = []
    for term in terms[:12]:
        like = f"%{term}%"
        clauses.append("(compiled_truth LIKE ? OR learned LIKE ? OR cause LIKE ? OR effect LIKE ? OR summary_struct LIKE ?)")
        params.extend([like] * 5)
    where = f" AND ({' OR '.join(clauses)})" if clauses else ""
    rows = conn.execute(f"""
        SELECT slug, type, title, summary_struct, compiled_truth, learned, cause, effect, updated_at
        FROM pages WHERE {_active_clause('pages')}{where}
        ORDER BY updated_at DESC LIMIT ?""", params + [max(20, limit * 4)]).fetchall()
    scored = []
    for row in rows:
        payload = _safe_json_loads(row["summary_struct"])
        for key in keys:
            values = payload.get(key) if isinstance(payload, dict) else None
            if isinstance(values, str) and values.strip():
                values = [values]
            if not isinstance(values, list):
                continue
            for value in values:
                if isinstance(value, dict):
                    text = value.get("atom") or value.get("content") or value.get("text") or json.dumps(value, ensure_ascii=False)
                    prefix = " ".join(str(value.get(k) or "") for k in ("date", "session_id", "role")).strip()
                    line = f"[{row['slug']}] {prefix} {text}".strip()
                else:
                    line = f"[{row['slug']}] {value}"
                overlap = _jaccard(question, line)
                term_hits = sum(1 for term in terms[:12] if term.lower() in line.lower())
                bonus = 0.2 if re.search(r"\d|\$", line) else 0
                if re.search(r"\bdr\.\s*[a-z]", line, re.I):
                    bonus += 2.0
                if any(x in line.lower() for x in ("primary care physician", "ent specialist", "dermatologist")):
                    bonus += 2.0
                if any(x in line.lower() for x in ("i'm not a doctor", "not a medical professional", "large language model")):
                    bonus -= 2.5
                if key in ("answer_plan", "proposed_answer"):
                    bonus -= 1.0
                if key == "timeline":
                    bonus += 0.5
                if overlap > 0 or term_hits or bonus > 0:
                    scored.append((overlap + term_hits * 0.5 + bonus, line))
    conn.close()
    if "timeline" in keys:
        scored.sort(key=lambda x: (_line_date_key(x[1]), x[0]), reverse=True)
    else:
        scored.sort(key=lambda x: x[0], reverse=True)
    return _unique_lines([line for _score, line in scored], limit)

def _beads_snapshot(cwd: Optional[str] = None) -> dict:
    """Read Beads state without mutating it. Missing bd/project is not an error."""
    if not shutil.which("bd"):
        return {"available": False, "reason": "bd not installed"}
    cwd = cwd or os.getcwd()
    snapshots = {}
    for name, args in {
        "ready": ["bd", "ready", "--json"],
        "list": ["bd", "list", "--json"],
    }.items():
        try:
            proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=10)
        except Exception as e:
            snapshots[name] = {"ok": False, "error": str(e)}
            continue
        if proc.returncode != 0:
            snapshots[name] = {"ok": False, "error": (proc.stderr or proc.stdout).strip()[:500]}
            continue
        try:
            data = json.loads(proc.stdout or "[]")
        except Exception:
            data = proc.stdout.strip()
        snapshots[name] = {"ok": True, "data": data}
    return {"available": True, "cwd": cwd, "snapshots": snapshots}

def build_cognitive_anchor(question: str, limit: int = 5, beads_cwd: Optional[str] = None) -> dict:
    """Build the R0/C1/I2 cognitive anchor used before reasoning."""
    results = search_with_activation(question, limit)
    causal = query_causal(question, limit)
    trace = trace_memory(question, depth=2, limit=limit)
    conn = get_db()
    profiles = conn.execute("""
        SELECT profile_type, key, value, evidence, confidence FROM profiles
        WHERE status='active' ORDER BY confidence DESC, updated_at DESC LIMIT ?""", (limit,)).fetchall()

    facts = _unique_lines([
        f"[{r.get('slug')}] {r.get('title') or ''} {r.get('snippet') or ''}" for r in results
    ], limit)
    rules = _unique_lines([
        f"[{p['profile_type']}] {p['key']} = {p['value']}" for p in profiles
    ], limit)
    decisions = _unique_lines([
        r.get("decided") or r.get("learned") or r.get("title") or "" for r in causal
    ], limit)
    field_lines = []
    for r in causal:
        slug = r.get("slug")
        for item in _normalize_causal_items(r.get("summary_struct"), r.get("cause"), r.get("effect")):
            label = "前因" if item["relation"] == "cause" else "后果"
            field_lines.append(f"[{slug}] {label}：{item['text']}")
    anchor_budget = {
        "direct_evidence": max(8, limit * 2),
        "causal_events": max(8, limit * 2),
        "timeline": max(8, limit * 2),
        "causal_chain": max(6, limit),
        "aggregation_candidates": max(4, limit),
        "answer_plan": min(3, max(1, limit // 2 + 1)),
        "proposed_answer": 1,
    }
    causal_lines = _rank_causal_anchor_lines(question, field_lines, trace, anchor_budget["causal_chain"])
    event_lines = _causal_event_anchor_lines(question, anchor_budget["causal_events"])
    belief_lines = _belief_anchor_lines(question, max(6, limit))
    belief_candidate_lines = _belief_candidate_anchor_lines(question, max(3, limit // 2 + 1))
    transition_lines = _transition_anchor_lines(question, max(6, limit))
    direct_evidence = _anchor_structured_lines(question, ("direct_evidence", "memory_atoms"), anchor_budget["direct_evidence"])
    aggregation_candidates = _anchor_structured_lines(question, ("aggregation_candidates",), anchor_budget["aggregation_candidates"])
    timeline = _anchor_structured_lines(question, ("timeline",), anchor_budget["timeline"])
    answer_plan = _anchor_structured_lines(question, ("answer_plan",), anchor_budget["answer_plan"])
    proposed_answers = _anchor_structured_lines(question, ("proposed_answer",), anchor_budget["proposed_answer"])

    beads = _beads_snapshot(beads_cwd)
    execution_status = []
    if beads.get("available"):
        ready = beads.get("snapshots", {}).get("ready", {})
        ready_data = ready.get("data") if ready.get("ok") else []
        if isinstance(ready_data, list):
            for item in ready_data[:limit]:
                if isinstance(item, dict):
                    bid = item.get("id") or item.get("issue_id") or "bd"
                    title = item.get("title") or item.get("description") or ""
                    execution_status.append(f"{bid}: {title}"[:220])
        elif ready.get("ok") and ready_data:
            execution_status.append(str(ready_data)[:220])
    elif beads.get("reason"):
        execution_status.append(f"Beads 未接入：{beads['reason']}")

    return {
        "question": question,
        "anchor": {
            "事实": facts,
            "规则": rules,
            "历史决策": decisions,
            "直接证据": direct_evidence,
            "时人事因果": event_lines,
            "聚合候选": aggregation_candidates,
            "时间线": timeline,
            "答案草稿": answer_plan,
            "建议答案": proposed_answers,
            "因果链": causal_lines,
            "意图/偏好线索": belief_lines,
            "待确认意图/偏好线索": belief_candidate_lines,
            "用户状态变化": transition_lines,
            "执行状态": execution_status[:limit],
            "判断约束": [
                "不要直接猜；先依据时人事因果、直接证据、时间线、因果链、上下文和状态变化判断。",
                "意图/偏好线索只用于辅助解释，不能替代时人事因果事件链。",
                "待确认意图/偏好线索只能作为提醒，不能当作事实；必须有进一步证据或确认后才能采用。",
                "涉及人物是谁、想要什么、为什么这么做时，先拉取该人物的时人事因果链，再由模型判断。",
                "涉及用户状态变化时，沿用户状态变化判断 before -> after、触发事件和原因。",
                "答案草稿/建议答案只可作为低权重假设；必须被直接证据和时间线支持后才能采用。",
                "时间冲突时优先使用带日期的较新直接证据；不能让答案草稿覆盖时间链。",
                "缺少证据时标记“待核实”。",
                "涉及执行进度时优先参考 Beads 状态；Beads 缺失时不要编造。",
            ],
        },
        "sources": {
            "search_results": [r.get("slug") for r in results],
            "causal_results": [r.get("slug") for r in causal],
            "beads": beads,
        },
    }

def _print_anchor(anchor: dict):
    print("<causamem-cognitive-anchor>")
    for key in ("事实", "规则", "历史决策", "直接证据", "时人事因果", "聚合候选", "时间线", "答案草稿", "建议答案", "因果链", "意图/偏好线索", "待确认意图/偏好线索", "用户状态变化", "执行状态", "判断约束"):
        print(f"{key}：")
        values = anchor.get("anchor", {}).get(key, [])
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- 待核实")
        print()
    print("</causamem-cognitive-anchor>")

def cmd_anchor():
    if len(sys.argv) < 3:
        print("Usage: gbrain anchor <question> [--json] [--beads-cwd PATH]"); sys.exit(1)
    args = sys.argv[2:]
    as_json = "--json" in args
    beads_cwd = None
    if "--beads-cwd" in args:
        idx = args.index("--beads-cwd")
        if idx + 1 >= len(args):
            print("Usage: gbrain anchor <question> [--json] [--beads-cwd PATH]"); sys.exit(1)
        beads_cwd = args[idx + 1]
        del args[idx:idx + 2]
    args = [a for a in args if a != "--json"]
    question = " ".join(args).strip()
    if not question:
        print("Usage: gbrain anchor <question> [--json] [--beads-cwd PATH]"); sys.exit(1)
    anchor = build_cognitive_anchor(question, beads_cwd=beads_cwd)
    if as_json:
        print(json.dumps(anchor, ensure_ascii=False, indent=2))
    else:
        _print_anchor(anchor)

def cmd_beads_capture():
    cwd = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    snapshot = _beads_snapshot(cwd)
    if not snapshot.get("available"):
        print(f"beads unavailable: {snapshot.get('reason', 'unknown')}")
        sys.exit(1)
    content = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    conn = get_db()
    existing = conn.execute("""
        SELECT id FROM raw_events
        WHERE source='beads' AND content=?
        ORDER BY created_at DESC LIMIT 1""", (content,)).fetchone()
    if existing:
        print(f"beads raw_event already captured: {existing['id']}")
        return
    event_id = capture_raw_event(
        content,
        role="system",
        source="beads",
        metadata={"kind": "execution-trace", "cwd": cwd})
    print(f"captured beads raw_event: {event_id}")

# ── Main ─────────────────────────────────────────────────────────────────────
USAGE = f"""
gbrain.py — GBrain Python Port v0.16 (enhanced)

Commands:
  init                    Initialize brain.db
  put <slug> [file.md]    Create/update page (plain)
  put-structured <slug> [file.md]  Create/update with AI compression; omit file to read stdin
  compress <text>          AI compress observation (print JSON)
  get <slug>              Show compiled truth + timeline + structured
  search <query>          FTS5 full-text search
  query <question>       Vector search + time decay + activation spread
  causal <keyword>        因果检索: search cause/effect fields
  migrate                 Apply schema upgrades and rebuild causal edges
  doctor                  Check DB/schema/embedding health
  backup                  Copy brain.db to timestamped backup
  eval [file.jsonl]       Run recall eval set
  capture <text>          Save L0 raw event
  extract                 Build L1 candidates from raw events
  import-candidates       Import L1 candidates from JSON stdin
  gate-candidates [limit] [--json] List candidates needing model gate
  apply-gates             Apply model gate JSON from stdin
  commit [--allow-ungated] Commit approved candidates into pages; ungated requires explicit flag
  scene <slug> <title>    Upsert scene
  attach-scene <scene> <page> Attach page to scene
  profile <type> <key> <value> Upsert profile fact
  profiles                List active profiles
  auto-classify [limit]   Auto-attach recent pages to scenes and update profiles
  trace <keyword>         Trace causal graph edges
  why <keyword>           Explain likely causal reason
  anchor <question>       Build CausaMem cognitive anchor before reasoning
  beads-capture [cwd]     Capture Beads execution state into R0 raw_events
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
    elif cmd == "doctor":
        cmd_doctor()
    elif cmd == "backup":
        cmd_backup()
    elif cmd == "migrate":
        cmd_migrate()
    elif cmd == "eval":
        cmd_eval(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "capture":
        cmd_capture()
    elif cmd == "extract":
        cmd_extract()
    elif cmd == "import-candidates":
        cmd_import_candidates()
    elif cmd == "gate-candidates":
        cmd_gate_candidates()
    elif cmd == "apply-gates":
        cmd_apply_gates()
    elif cmd == "commit":
        cmd_commit()
    elif cmd == "scene":
        cmd_scene()
    elif cmd == "attach-scene":
        cmd_attach_scene()
    elif cmd == "profile":
        cmd_profile()
    elif cmd == "profiles":
        cmd_profiles()
    elif cmd == "auto-classify":
        cmd_auto_classify()
    elif cmd == "trace":
        cmd_trace()
    elif cmd == "why":
        cmd_why()
    elif cmd == "anchor":
        cmd_anchor()
    elif cmd == "beads-capture":
        cmd_beads_capture()
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
