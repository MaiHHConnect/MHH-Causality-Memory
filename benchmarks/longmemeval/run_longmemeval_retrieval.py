#!/usr/bin/env python3
"""Local LongMemEval retrieval benchmark for CausaMem-style memory retrieval.

This runner is intentionally dependency-light. It evaluates whether the memory
retrieval layer can bring the evidence session(s) into the top-k context.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1]


def session_text(session: list[dict], user_only: bool = False) -> str:
    parts = []
    for turn in session:
        if user_only and turn.get("role") != "user":
            continue
        parts.append(f"{turn.get('role', '')}: {turn.get('content', '')}")
    return "\n".join(parts)


def score_sessions(question: str, sessions: list[list[dict]], user_only: bool = False) -> list[tuple[int, float]]:
    q_tokens = tokens(question)
    if not q_tokens:
        return [(i, 0.0) for i in range(len(sessions))]

    docs = [tokens(session_text(s, user_only=user_only)) for s in sessions]
    df = defaultdict(int)
    for doc in docs:
        for t in set(doc):
            df[t] += 1
    n_docs = max(1, len(docs))
    avgdl = sum(len(d) for d in docs) / n_docs if docs else 1.0
    q_counts = Counter(q_tokens)

    ranked = []
    for i, doc in enumerate(docs):
        counts = Counter(doc)
        dl = max(1, len(doc))
        score = 0.0
        for t, qtf in q_counts.items():
            tf = counts.get(t, 0)
            if not tf:
                continue
            idf = math.log(1 + (n_docs - df[t] + 0.5) / (df[t] + 0.5))
            denom = tf + 1.5 * (1 - 0.75 + 0.75 * dl / max(avgdl, 1.0))
            score += idf * (tf * 2.5 / denom) * min(qtf, 3)
        ranked.append((i, score))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def reciprocal_rank(ranked_ids: list[str], answer_ids: set[str]) -> float:
    for rank, sid in enumerate(ranked_ids, 1):
        if sid in answer_ids:
            return 1.0 / rank
    return 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="benchmarks/longmemeval/data/longmemeval_oracle.json")
    ap.add_argument("--out", default="benchmarks/longmemeval/results/oracle_retrieval_results.json")
    ap.add_argument("--user-only", action="store_true")
    args = ap.parse_args()

    data_path = Path(args.data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(data_path.read_text(encoding="utf-8"))

    metrics = {"hit@1": 0, "hit@3": 0, "hit@5": 0, "hit@10": 0, "mrr": 0.0}
    by_type = defaultdict(lambda: {"n": 0, "hit@1": 0, "hit@3": 0, "hit@5": 0, "hit@10": 0, "mrr": 0.0})
    rows = []
    evaluated = 0

    for item in data:
        qid = item["question_id"]
        if qid.endswith("_abs"):
            continue
        answer_ids = set(item.get("answer_session_ids") or [])
        if not answer_ids:
            continue
        session_ids = item["haystack_session_ids"]
        ranked = score_sessions(item["question"], item["haystack_sessions"], user_only=args.user_only)
        ranked_ids = [session_ids[i] for i, _score in ranked]
        rr = reciprocal_rank(ranked_ids, answer_ids)
        evaluated += 1
        qtype = item.get("question_type", "unknown")
        by_type[qtype]["n"] += 1
        for k in (1, 3, 5, 10):
            hit = int(any(sid in answer_ids for sid in ranked_ids[:k]))
            metrics[f"hit@{k}"] += hit
            by_type[qtype][f"hit@{k}"] += hit
        metrics["mrr"] += rr
        by_type[qtype]["mrr"] += rr
        rows.append({
            "question_id": qid,
            "question_type": qtype,
            "answer_session_ids": sorted(answer_ids),
            "top10": ranked_ids[:10],
            "rr": rr,
        })

    summary = {"dataset": str(data_path), "cases": evaluated, "skipped_abstention_or_no_answer": len(data) - evaluated}
    for key, val in metrics.items():
        summary[key] = round(val / evaluated, 4) if evaluated else 0.0
    summary["by_type"] = {}
    for qtype, vals in sorted(by_type.items()):
        n = vals.pop("n")
        summary["by_type"][qtype] = {"n": n, **{k: round(v / n, 4) for k, v in vals.items()}}

    out_path.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
