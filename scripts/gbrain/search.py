#!/usr/bin/env python3
"""
gbrain_search.py — OpenClaw fallback search
当 memory_search 结果少时，调用此脚本查询 gbrain
用法: python3 gbrain_search.py <query>
"""
import sqlite3, os, sys, struct, requests

GBRAIN_DB = os.environ.get("GBRAIN_DB", os.path.join(os.path.dirname(__file__), "brain.db"))
SF_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

def get_embedding(text: str) -> list[float]:
    resp = requests.post(
        "https://api.siliconflow.cn/v1/embeddings",
        headers={"Authorization": f"Bearer {SF_KEY}", "Content-Type": "application/json"},
        json={"model": "Qwen/Qwen3-Embedding-8B", "input": text[:3000]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def cosine_sim(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    norm = (sum(x*x for x in a)**0.5) * (sum(x*x for x in b)**0.5)
    return dot/norm if norm else 0

def bytes_to_f32(data):
    return list(struct.unpack(f"{len(data)//4}f", data))

def search_fts(query, limit=5):
    conn = sqlite3.connect(GBRAIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT slug, title, snippet(page_fts_idx, 2, '**', '**', '...', 30) AS snippet
        FROM page_fts_idx WHERE page_fts_idx MATCH ?
        ORDER BY rank LIMIT ?
    """, (query, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_vector(query, limit=5):
    try:
        q_emb = get_embedding(query)
    except Exception as e:
        print(f"# vector embed error: {e}", file=sys.stderr)
        return []
    conn = sqlite3.connect(GBRAIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT page_id, embedding FROM page_embeddings").fetchall()
    results = []
    for page_id, emb_bytes in rows:
        emb = bytes_to_f32(emb_bytes)
        sim = cosine_sim(q_emb, emb)
        page = conn.execute("SELECT slug, title FROM pages WHERE id=?", (page_id,)).fetchone()
        if page:
            results.append({"slug": page["slug"], "title": page["title"], "score": sim})
    conn.close()
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: gbrain_search.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"# Query: {query}\n")

    fts_results = search_fts(query, limit=5)
    vec_results = search_vector(query, limit=5)

    print("## FTS5 Results")
    if fts_results:
        for r in fts_results:
            print(f"  [{r['slug']}] {r['title'] or ''}")
            if r.get('snippet'):
                print(f"    {r['snippet']}")
    else:
        print("  (none)")

    print("\n## Vector Results")
    if vec_results:
        for r in vec_results:
            print(f"  [{r['slug']}] {r['title'] or ''} (score={r['score']:.3f})")
    else:
        print("  (none)")
