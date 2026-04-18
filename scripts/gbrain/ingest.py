#!/usr/bin/env python3
"""Bulk ingest .md files into gbrain brain.db"""
import sqlite3, os, sys, re, glob, hashlib
import requests

GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.join(os.path.dirname(__file__), "brain.db"))
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SF_API = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"

def get_db():
    conn = sqlite3.connect(GBRAIN_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_embedding(text: str) -> list[float]:
    resp = requests.post(
        f"{SF_API}/embeddings",
        headers={"Authorization": f"Bearer {SILICONFLOW_KEY}", "Content-Type": "application/json"},
        json={"model": EMBEDDING_MODEL, "input": text[:3000]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-")).strip("-")

def extract_sections(content: str):
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

def build_compiled_truth(sections):
    lines = []
    for header, body in sections:
        if header:
            lines.append(f"## {header}")
        first_para = body.split("\n\n")[0].strip()
        if first_para:
            lines.append(first_para)
    return "\n\n".join(lines)

def build_timeline(sections):
    entries = []
    for header, body in sections:
        meta = f"## {header}" if header else "## (intro)"
        entries.append(meta)
        entries.append(body)
    return "\n\n".join(entries)

def extract_links(content: str) -> list[str]:
    wl = re.findall(r'\[\[([^\]]+)\]\]', content)
    ml = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
    return [slugify(l) for l in wl + ml]

def float32_to_bytes(vec):
    import struct
    return b"".join(struct.pack("f", v) for v in vec)

def ingest_file(filepath: str, slug: str):
    with open(filepath) as f:
        content = f.read()
    sections = extract_sections(content)
    compiled = build_compiled_truth(sections)
    timeline = build_timeline(sections)
    title = sections[0][1].split("\n")[0][:80] if sections else slug

    conn = get_db()
    now = "datetime('now')"
    conn.execute("""
        INSERT INTO pages (slug, type, title, compiled_truth, timeline, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title, compiled_truth=excluded.compiled_truth,
            timeline=excluded.timeline, updated_at=datetime('now')
    """, (slug, "source", title, compiled, timeline))
    page_id = conn.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone()["id"]

    # FTS
    conn.execute("DELETE FROM page_fts WHERE page_id=?", (page_id,))
    conn.execute("INSERT INTO page_fts (page_id, slug, title, body) VALUES (?,?,?,?)",
                 (page_id, slug, title, content))

    # Links
    conn.execute("DELETE FROM links WHERE from_page=?", (page_id,))
    for link_target in extract_links(content):
        conn.execute("INSERT INTO links (from_page, to_slug) VALUES (?,?)", (page_id, link_target))

    # Embedding
    emb = get_embedding((compiled + "\n\n" + timeline)[:3000])
    emb_bytes = float32_to_bytes(emb)
    conn.execute("DELETE FROM page_embeddings WHERE page_id=?", (page_id,))
    conn.execute("INSERT INTO page_embeddings (page_id, embedding) VALUES (?,?)",
                 (page_id, emb_bytes))
    conn.commit()
    conn.close()
    return slug, title

if __name__ == "__main__":
    wiki_sources = os.environ.get("WIKI_SOURCES", os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki/main/sources"))
    files = glob.glob(f"{wiki_sources}/*.md")
    print(f"Found {len(files)} .md files in {wiki_sources}")

    success = 0
    failed = []
    for filepath in sorted(files):
        slug = slugify(os.path.splitext(os.path.basename(filepath))[0])
        try:
            slug, title = ingest_file(filepath, slug)
            print(f"  ✓ {slug}")
            success += 1
        except Exception as e:
            print(f"  ✗ {filepath}: {e}")
            failed.append(filepath)

    print(f"\nDone: {success} ok, {len(failed)} failed")
    if failed:
        print("Failed files:")
        for f in failed:
            print(f"  {f}")
