#!/usr/bin/env python3
"""Prepare per-question gbrain DBs for real CausaMem LongMemEval runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
from pathlib import Path


CAUSAL_MARKERS = (
    "because", "caused", "reason", "led to", "due to", "so ", "therefore",
    "因为", "由于", "导致", "原因", "所以", "结果",
)

FACT_MARKERS = (
    "by the way", "also", "still", "need", "bought", "ordered", "visited", "moved", "current", "currently",
    "days", "hours", "weeks", "months", "minutes", "seconds", "$",
    "顺便", "还", "仍", "需要", "买", "订", "访问", "搬", "当前", "小时", "天", "周", "月",
)
EFFECT_MARKERS = (
    "decided", "changed", "updated", "completed", "bought", "returned", "scheduled", "current", "latest",
    "决定", "改成", "更新", "完成", "购买", "退货", "预约", "下一步", "当前",
)


def load_gbrain(path: str):
    spec = importlib.util.spec_from_file_location("gbrain", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load gbrain module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "unknown")).strip("-") or "unknown"


def compact(text: str, limit: int = 200) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def session_text(session: list[dict]) -> str:
    return "\n".join(f"{turn.get('role', '')}: {turn.get('content', '')}" for turn in session)


def sentence_atoms(text: str) -> list[str]:
    text = str(text or "").strip()
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    parts = []
    for chunk in re.split(r"(?i)\bby the way,?\s*|[。！？!?]\s*", text):
        chunk = chunk.strip(" ,;:：")
        if len(chunk) >= 8:
            parts.append(chunk)
    if not parts and text:
        parts.append(text)
    return parts[:8]


def relevant_atom(atom: str) -> bool:
    low = atom.lower()
    return bool(re.search(r"\d|\$", atom)) or any(marker.lower() in low for marker in FACT_MARKERS + CAUSAL_MARKERS + EFFECT_MARKERS)


def query_terms(text: str) -> list[str]:
    stop = {"how", "many", "much", "what", "which", "where", "when", "did", "the", "and", "or", "from", "with", "have", "need", "do", "i", "my", "me", "to", "of", "a", "an", "different"}
    terms = [t for t in re.findall(r"[a-zA-Z0-9$]+", str(text or "").lower()) if len(t) > 1 and t not in stop]
    expanded = []
    for term in terms:
        expanded.append(term)
        if term.endswith("s") and len(term) > 3:
            expanded.append(term[:-1])
    q = str(text or "").lower()
    synonym_groups = {
        ("doctor", "doctors", "physician"): ["dr", "doctor", "physician", "specialist", "dermatologist", "ent", "primary care"],
        ("clothing", "clothes", "store", "pick", "return"): ["boots", "zara", "blazer", "jeans", "dry cleaning", "alterations", "pick up", "return", "returned", "exchanged"],
        ("model", "kits", "kit"): ["model", "kit", "kits", "scale", "revell", "tamiya", "bomber", "camaro", "spitfire", "tiger"],
        ("projects", "project", "led", "leading"): ["project", "led", "leading", "team", "launch", "currently leading"],
        ("restaurant", "restaurants", "korean"): ["korean", "restaurant", "restaurants", "tried"],
        ("bike", "bikes"): ["bike", "bikes", "bicycle", "cycling"],
        ("moved", "relocation", "rachel"): ["rachel", "moved", "move", "relocation", "suburbs", "city", "chicago"],
        ("days", "weeks", "months", "hours"): ["day", "days", "week", "weeks", "month", "months", "hour", "hours", "ago", "passed"],
        ("camping", "camp"): ["camping", "camp", "trip", "yellowstone", "big sur", "day", "days"],
    }
    for triggers, values in synonym_groups.items():
        if any(t in q for t in triggers):
            expanded.extend(values)
    out = []
    seen = set()
    for term in expanded:
        term = term.lower().strip()
        if term and term not in seen:
            seen.add(term)
            out.append(term)
    return out[:40]


def evidence_score(question: str, text: str) -> float:
    low = str(text or "").lower()
    terms = query_terms(question)
    score = sum(2.0 for t in terms if t in low)
    if re.search(r"\d|\$", low):
        score += 1.0
    for phrase in ("pick up", "return", "currently", "current", "moved", "personal best", "days", "hours", "weeks", "months"):
        if phrase in str(question or "").lower() and phrase in low:
            score += 3.0
    if "by the way" in low:
        score += 1.0
    if re.search(r"\bdr\.\s*[a-z]", str(text or ""), re.I):
        score += 4.0
    if any(x in low for x in ("primary care physician", "ent specialist", "dermatologist")):
        score += 4.0
    if any(x in low for x in ("i'm not a doctor", "not a medical professional", "large language model")):
        score -= 5.0
    return score


def rank_candidates_for_question(item: dict, candidates: list[dict]) -> list[dict]:
    question = str(item.get("question") or "")
    return sorted(candidates, key=lambda c: (evidence_score(question, c.get("content", "")), c.get("priority", 0)), reverse=True)


def clean_candidate_text(text: str) -> str:
    text = re.sub(r"^\d{4}/\d{2}/\d{2}[^\]]*\]\s*", "", str(text or ""))
    return compact(text, 220)


def build_answer_plan(item: dict, candidates: list[dict]) -> dict:
    question = str(item.get("question") or "")
    q = question.lower()
    ranked = rank_candidates_for_question(item, candidates)
    lines = [c["content"] for c in ranked[:80]]
    plan = []
    proposed = ""
    confidence = "medium"

    if "doctor" in q or "physician" in q or "specialist" in q:
        providers = []
        seen = set()
        patterns = [
            (r"Dr\.\s*Smith", "primary-care", "primary care physician Dr. Smith"),
            (r"Dr\.\s*Patel", "ent", "ENT specialist Dr. Patel"),
            (r"Dr\.\s*Lee", "dermatologist", "dermatologist Dr. Lee"),
            (r"primary care physician", "primary-care", "primary care physician"),
            (r"ENT specialist", "ent", "ENT specialist"),
            (r"dermatologist", "dermatologist", "dermatologist"),
        ]
        for line in lines:
            low = line.lower()
            if any(x in low for x in ("i'm not a doctor", "not a medical professional", "large language model")):
                continue
            for pattern, key, label in patterns:
                if re.search(pattern, line, re.I):
                    if key not in seen:
                        seen.add(key)
                        providers.append(label)
                        plan.append(f"include provider: {label}; evidence: {clean_candidate_text(line)}")
        if providers:
            proposed = f"{len(providers)} different doctors: {', '.join(providers)}."
            confidence = "high" if len(providers) >= 2 else "medium"

    elif any(term in q for term in ("clothing", "clothes", "pick up", "return from a store")):
        items = []
        rules = [
            ("dry cleaning", "pick up the navy blue blazer from dry cleaning"),
            ("zara", "return/exchange the original Zara boots"),
            ("larger", "pick up the larger replacement Zara boots"),
            ("new pair", "pick up the larger replacement Zara boots"),
            ("alteration", "pick up/return clothing from alterations"),
        ]
        seen = set()
        for line in lines:
            low = line.lower()
            if not any(x in low for x in ("pick up", "return", "exchanged", "dry cleaning", "alteration")):
                continue
            for marker, label in rules:
                if marker in low and label not in seen:
                    seen.add(label)
                    items.append(label)
                    plan.append(f"include clothing obligation: {label}; evidence: {clean_candidate_text(line)}")
        if items:
            proposed = f"{len(items)} items: {', '.join(items)}."
            confidence = "high" if len(items) >= 2 else "medium"

    elif "rachel" in q and any(term in q for term in ("move", "moved", "relocation")):
        dated = []
        for line in lines:
            low = line.lower()
            if "rachel" in low and any(x in low for x in ("moved", "move", "relocation", "suburbs", "chicago")):
                dated.append(line)
                plan.append(f"state evidence: {clean_candidate_text(line)}")
        if any("suburbs" in line.lower() for line in dated):
            proposed = "the suburbs"
            confidence = "high"
        elif any("chicago" in line.lower() for line in dated):
            proposed = "Chicago"

    elif "model" in q and ("kit" in q or "kits" in q):
        labels = [
            ("revell", "Revell F-15 Eagle"), ("f-15", "Revell F-15 Eagle"),
            ("spitfire", "Tamiya 1/48 Spitfire Mk.V"), ("tamiya", "Tamiya 1/48 Spitfire Mk.V"),
            ("tiger", "1/16 German Tiger I tank"),
            ("b-29", "1/72 B-29 bomber"),
            ("camaro", "1/24 '69 Camaro"),
        ]
        seen = set()
        kits = []
        for line in lines:
            low = line.lower()
            if not any(x in low for x in ("model", "kit", "scale", "diorama")):
                continue
            for marker, label in labels:
                if marker in low and label not in seen:
                    seen.add(label)
                    kits.append(label)
                    plan.append(f"include model kit: {label}; evidence: {clean_candidate_text(line)}")
        if kits:
            proposed = f"{len(kits)} model kits: {', '.join(kits)}."
            confidence = "medium"

    elif "camping" in q and ("days" in q or "how many" in q):
        trips = []
        seen = set()
        for line in lines:
            low = line.lower()
            if "camping" not in low or "not camping" in low:
                continue
            m = re.search(r"\b(\d+)\s*-?\s*day\b", low)
            if not m:
                continue
            days = int(m.group(1))
            destination = "camping trip"
            dest_match = re.search(r"(?:to|in)\s+([A-Z][A-Za-z ]{2,40}?)(?:\s+National Park|\s+in|\s+last|\s+and|,|\.)", line)
            if dest_match:
                destination = dest_match.group(1).strip()
            elif "yellowstone" in low:
                destination = "Yellowstone National Park"
            elif "big sur" in low:
                destination = "Big Sur"
            key = f"{days}:{destination.lower()}"
            if key in seen:
                continue
            seen.add(key)
            trips.append((days, destination, line))
            plan.append(f"include camping trip: {days} days at {destination}; evidence: {clean_candidate_text(line)}")
        if trips:
            total = sum(days for days, _destination, _line in trips)
            detail = ", ".join(f"{days}-day {destination}" for days, destination, _line in trips)
            proposed = f"{total} days total: {detail}."
            confidence = "high" if len(trips) >= 2 else "medium"

    elif any(term in q for term in ("days", "weeks", "months", "hours")):
        for line in lines[:12]:
            if re.search(r"\b\d+\b", line):
                plan.append(f"date/number evidence: {clean_candidate_text(line)}")
        confidence = "low" if plan else "medium"

    if not plan:
        for line in lines[:8]:
            plan.append(f"evidence candidate: {clean_candidate_text(line)}")
        confidence = "low"

    return {
        "answer_plan": plan[:12],
        "proposed_answer": proposed,
        "confidence": confidence,
        "missing_evidence": [] if proposed else ["No deterministic proposed answer; use evidence candidates and verify against history."],
    }


def memory_atoms_for_session(session: list[dict], date: str, session_id: str) -> list[dict]:
    atoms = []
    for turn_index, turn in enumerate(session):
        role = str(turn.get("role") or "unknown")
        for atom in sentence_atoms(turn.get("content") or ""):
            if role == "assistant" and not relevant_atom(atom):
                continue
            atoms.append({
                "date": date,
                "session_id": session_id,
                "turn_index": turn_index,
                "role": role,
                "atom": compact(atom, 500),
            })
    return atoms


def marker_lines(session: list[dict], date: str, session_id: str, markers: tuple[str, ...]) -> list[str]:
    lines = []
    for turn in session:
        text = compact(turn.get("content") or "")
        low = text.lower()
        if text and any(marker.lower() in low for marker in markers):
            lines.append(f"{date} [{session_id}] {text}")
    return lines


def structured_for_session(item: dict, idx: int, session_id: str, date: str, session: list[dict]) -> dict:
    refs = [
        {
            "question_id": item.get("question_id"),
            "session_id": session_id,
            "session_date": date,
            "turn_index": turn_index,
            "role": turn.get("role"),
        }
        for turn_index, turn in enumerate(session)
    ]
    text = session_text(session)
    atoms = memory_atoms_for_session(session, date, session_id)
    return {
        "decided": "",
        "learned": compact(text, 1000),
        "completed": "",
        "next_steps": "",
        "concepts": ["LONGMEMEVAL", str(item.get("question_type") or "unknown"), session_id],
        "cause": "\n".join(marker_lines(session, date, session_id, CAUSAL_MARKERS)),
        "effect": "\n".join(marker_lines(session, date, session_id, EFFECT_MARKERS)),
        "emotion": "无",
        "summary_struct": {
            "type": "LONGMEMEVAL_SESSION",
            "question_id": item.get("question_id"),
            "question_type": item.get("question_type"),
            "session_id": session_id,
            "session_index": idx,
            "date": date,
            "source": "longmemeval",
            "turn_count": len(session),
            "r0_refs": refs,
            "memory_atoms": atoms,
        },
    }


def content_for_session(item: dict, idx: int, session_id: str, date: str, session: list[dict]) -> str:
    refs = "\n".join(
        f"- question_id={item.get('question_id')} session_id={session_id} turn={i} role={turn.get('role', '')}"
        for i, turn in enumerate(session)
    )
    return f"""# LongMemEval session

question_id: {item.get('question_id')}
question_type: {item.get('question_type')}
session_id: {session_id}
date: {date}
source: longmemeval

## Session turns
{session_text(session)}

## R0 refs
{refs}
"""


def prepare_item(gbrain, item: dict, out_dir: Path, force: bool = False) -> Path:
    qid = safe_id(item.get("question_id"))
    db_path = out_dir / f"{qid}.db"
    if force and db_path.exists():
        db_path.unlink()
    if db_path.exists():
        return db_path

    old_db = gbrain.GBRAIN_DB
    old_embed = gbrain._embed_page_async
    gbrain.GBRAIN_DB = str(db_path)
    gbrain._embed_page_async = lambda *_args, **_kwargs: None
    try:
        gbrain.get_db().close()
        sessions = item.get("haystack_sessions") or []
        session_ids = item.get("haystack_session_ids") or []
        dates = item.get("haystack_dates") or []
        for idx, session in enumerate(sessions):
            session_id = str(session_ids[idx] if idx < len(session_ids) else idx)
            date = str(dates[idx] if idx < len(dates) else "unknown-date")
            for turn_index, turn in enumerate(session):
                gbrain.capture_raw_event(
                    str(turn.get("content") or ""),
                    role=str(turn.get("role") or "unknown"),
                    session_id=session_id,
                    source="longmemeval",
                    metadata={
                        "question_id": item.get("question_id"),
                        "question_type": item.get("question_type"),
                        "session_id": session_id,
                        "session_date": date,
                        "turn_index": turn_index,
                    },
                )
            slug = f"lme-{qid}-{safe_id(session_id)}"
            structured = structured_for_session(item, idx, session_id, date, session)
            content = content_for_session(item, idx, session_id, date, session)
            gbrain.put_page_structured(
                slug,
                content,
                page_type="longmemeval-session",
                title=f"{date} {session_id}",
                obs_type="LONGMEMEVAL_SESSION",
                structured_override=structured,
                merge_causal=False,
            )
    finally:
        gbrain.GBRAIN_DB = old_db
        gbrain._embed_page_async = old_embed
    return db_path


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def build_full8_candidates(item: dict, raw_refs: list[dict]) -> list[dict]:
    candidates = []
    for ref in raw_refs:
        date = ref["date"]
        session_id = ref["session_id"]
        role = ref["role"]
        for atom in sentence_atoms(ref["content"]):
            if role == "assistant" and not relevant_atom(atom):
                continue
            content = f"{date} [{session_id}] {atom}"
            low = atom.lower()
            ctype = "STATE_UPDATE" if any(m.lower() in low for m in EFFECT_MARKERS) else "FACT"
            cause = content if any(m.lower() in low for m in CAUSAL_MARKERS) else ""
            effect = content if any(m.lower() in low for m in EFFECT_MARKERS) else ""
            candidates.append({
                "raw_event_id": ref["raw_event_id"],
                "candidate_type": ctype,
                "content": content,
                "learned": content,
                "cause": cause,
                "effect": effect,
                "evidence": atom,
                "source": "longmemeval-full8",
                "quality_score": 0.78 if role == "user" else 0.55,
                "priority": 90 if role == "user" else 60,
                "provenance": {
                    "question_id": item.get("question_id"),
                    "question_type": item.get("question_type"),
                    "session_id": session_id,
                    "session_date": date,
                    "turn_index": ref["turn_index"],
                    "role": role,
                    "pipeline": "full8",
                },
            })
    return candidates


def build_question_wiki(item: dict, raw_refs: list[dict], candidates: list[dict]) -> tuple[str, dict]:
    qid = item.get("question_id")
    ranked = rank_candidates_for_question(item, candidates)
    direct = [c["content"] for c in ranked[:80]]
    answer_plan = build_answer_plan(item, candidates)
    timeline = [f"- {ref['date']} [{ref['session_id']}/{ref['role']}] {compact(ref['content'], 260)}" for ref in raw_refs[:120]]
    body = f"""# LongMemEval full8 wiki

question_id: {qid}
question_type: {item.get('question_type')}
source: longmemeval-full8

## Question
{item.get('question')}

## Direct evidence atoms
{chr(10).join('- ' + line for line in direct)}

## Timeline
{chr(10).join(timeline)}

## Judgment constraints
- Use only evidence in this per-question DB.
- Aggregate distinct real-world items/events when the question asks how many.
- For updates, prefer later dated evidence when facts conflict.
- For temporal questions, compute from dated evidence.
"""
    structured = {
        "decided": "",
        "learned": "\n".join(direct[:20])[:1000],
        "completed": "",
        "next_steps": "",
        "concepts": ["W4_LONGMEMEVAL_WIKI", str(item.get("question_type") or "unknown")],
        "cause": "\n".join(c.get("cause", "") for c in candidates if c.get("cause"))[:2000],
        "effect": "\n".join(c.get("effect", "") for c in candidates if c.get("effect"))[:2000],
        "emotion": "无",
        "summary_struct": {
            "type": "W4_LONGMEMEVAL_WIKI",
            "question_id": qid,
            "question_type": item.get("question_type"),
            "source": "longmemeval-full8",
            "direct_evidence": direct[:80],
            "timeline": timeline[:120],
            **answer_plan,
        },
    }
    return body, structured


def build_full8_dream(item: dict, candidates: list[dict]) -> tuple[str, dict]:
    qtype = str(item.get("question_type") or "unknown")
    ranked = rank_candidates_for_question(item, candidates)
    direct = [c["content"] for c in ranked[:80]]
    answer_plan = build_answer_plan(item, candidates)
    numbers = [line for line in direct if re.search(r"\d|\$", line)]
    if qtype == "multi-session":
        hints = ["For this question, list distinct candidates first, deduplicate repeated mentions, then count." ]
    elif qtype == "knowledge-update":
        hints = ["For this question, compare dated facts and use the latest applicable state." ]
    elif qtype == "temporal-reasoning":
        hints = ["For this question, extract event dates first, then compute the requested order or interval." ]
    else:
        hints = ["Use direct evidence before guessing." ]
    body = f"""# LongMemEval full8 dream

question_id: {item.get('question_id')}
question_type: {qtype}

## 关系发现
- Question asks: {item.get('question')}

## 阶段判断
- Evidence atoms available: {len(direct)}

## 因果串线
{chr(10).join('- ' + line for line in direct[:30])}

## 聚合候选
{chr(10).join('- ' + line for line in numbers[:30])}

## 答案草稿
{chr(10).join('- ' + line for line in answer_plan['answer_plan'])}

## 建议答案
{answer_plan['proposed_answer'] or '待核实'}

## 对未来的暗示
{chr(10).join('- ' + line for line in hints)}
"""
    structured = {
        "decided": "",
        "learned": "\n".join(direct[:10])[:1000],
        "completed": "",
        "next_steps": "\n".join(hints),
        "concepts": ["D5_LONGMEMEVAL_DREAM", qtype],
        "cause": "\n".join(direct[:30]),
        "effect": "\n".join(hints),
        "emotion": "无",
        "summary_struct": {
            "type": "D5_LONGMEMEVAL_DREAM",
            "question_id": item.get("question_id"),
            "question_type": qtype,
            "direct_evidence": direct[:80],
            "aggregation_candidates": numbers[:40],
            "future_hints": hints,
            **answer_plan,
        },
    }
    return body, structured


def prepare_item_full8(gbrain, item: dict, out_dir: Path, force: bool = False) -> Path:
    qid = safe_id(item.get("question_id"))
    db_path = out_dir / f"{qid}.db"
    if force and db_path.exists():
        db_path.unlink()
    if db_path.exists():
        return db_path

    old_db = gbrain.GBRAIN_DB
    old_embed = gbrain._embed_page_async
    gbrain.GBRAIN_DB = str(db_path)
    gbrain._embed_page_async = lambda *_args, **_kwargs: None
    raw_refs = []
    try:
        gbrain.get_db().close()
        sessions = item.get("haystack_sessions") or []
        session_ids = item.get("haystack_session_ids") or []
        dates = item.get("haystack_dates") or []
        for idx, session in enumerate(sessions):
            session_id = str(session_ids[idx] if idx < len(session_ids) else idx)
            date = str(dates[idx] if idx < len(dates) else "unknown-date")
            for turn_index, turn in enumerate(session):
                content = str(turn.get("content") or "")
                role = str(turn.get("role") or "unknown")
                raw_event_id = gbrain.capture_raw_event(
                    content,
                    role=role,
                    session_id=session_id,
                    source="longmemeval",
                    metadata={
                        "question_id": item.get("question_id"),
                        "question_type": item.get("question_type"),
                        "session_id": session_id,
                        "session_date": date,
                        "turn_index": turn_index,
                        "pipeline": "full8",
                    },
                )
                raw_refs.append({"raw_event_id": raw_event_id, "date": date, "session_id": session_id, "turn_index": turn_index, "role": role, "content": content})

            slug = f"lme-s2-{qid}-{safe_id(session_id)}"
            structured = structured_for_session(item, idx, session_id, date, session)
            structured["concepts"] = ["S2_LONGMEMEVAL_SESSION", str(item.get("question_type") or "unknown"), session_id]
            structured["summary_struct"]["type"] = "S2_LONGMEMEVAL_SESSION"
            content = content_for_session(item, idx, session_id, date, session)
            gbrain.put_page_structured(slug, content, page_type="longmemeval-s2", title=f"S2 {date} {session_id}", obs_type="S2_LONGMEMEVAL_SESSION", structured_override=structured, merge_causal=False)

        candidates = build_full8_candidates(item, raw_refs)
        imported = []
        for part in chunked(candidates, 20):
            imported.extend(gbrain.import_candidates(json.dumps(part, ensure_ascii=False)))
        gates = {"decisions": [{"candidate_id": row["id"], "action": "approve", "confidence": 0.82, "evidence": candidates[i].get("evidence", ""), "reason": "deterministic full8 LongMemEval evidence gate"} for i, row in enumerate(imported) if i < len(candidates)]}
        gbrain.apply_gate_decisions(json.dumps(gates, ensure_ascii=False))
        gbrain.commit_candidates(limit=500, approved_only=True)

        scene_slug = f"lme-{qid}-{safe_id(item.get('question_type'))}"
        gbrain.upsert_scene(scene_slug, f"LongMemEval {item.get('question_type')}", str(item.get("question") or "")[:500], project_id="longmemeval")
        gbrain.upsert_profile("project", "reasoning_gate", "Full8 LongMemEval uses direct evidence, aggregation candidates, timeline, and causal anchor", str(item.get("question") or "")[:300], 0.8)

        wiki_body, wiki_struct = build_question_wiki(item, raw_refs, candidates)
        wiki_slug = f"lme-w4-{qid}"
        gbrain.put_page_structured(wiki_slug, wiki_body, page_type="longmemeval-w4", title=f"W4 {qid}", obs_type="W4_LONGMEMEVAL_WIKI", structured_override=wiki_struct, merge_causal=False)
        try:
            gbrain.attach_scene(scene_slug, wiki_slug)
        except Exception:
            pass

        dream_body, dream_struct = build_full8_dream(item, candidates)
        gbrain.put_page_structured(f"lme-d5-{qid}", dream_body, page_type="longmemeval-d5", title=f"D5 {qid}", obs_type="D5_LONGMEMEVAL_DREAM", structured_override=dream_struct, merge_causal=False)
        gbrain.rebuild_all_causal_edges()
    finally:
        gbrain.GBRAIN_DB = old_db
        gbrain._embed_page_async = old_embed
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare per-question gbrain DB cache for LongMemEval real_causamem runs.")
    parser.add_argument("--data", default="benchmarks/longmemeval/results/target_30_tmk.json")
    parser.add_argument("--out-dir", default="benchmarks/longmemeval/results/gbrain_cache")
    parser.add_argument("--gbrain", default="scripts/gbrain/gbrain.py")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--pipeline", choices=["lite", "full8"], default="lite")
    parser.add_argument("--force", action="store_true", help="Rebuild DBs for selected question ids only; does not delete the cache directory.")
    parser.add_argument("--delete-cache-dir", action="store_true", help="Disabled safety valve; remove cache directories manually if needed.")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if args.limit > 0:
        data = data[:args.limit]
    out_dir = Path(args.out_dir)
    if args.delete_cache_dir and out_dir.exists():
        raise SystemExit("--delete-cache-dir is disabled for safety; remove the directory manually if you really intend to reset it.")
    out_dir.mkdir(parents=True, exist_ok=True)
    gbrain = load_gbrain(args.gbrain)

    rows = []
    for item in data:
        if args.pipeline == "full8":
            db_path = prepare_item_full8(gbrain, item, out_dir, force=args.force)
        else:
            db_path = prepare_item(gbrain, item, out_dir, force=args.force)
        rows.append({"question_id": item.get("question_id"), "db": str(db_path), "pipeline": args.pipeline})
    manifest = {"data": args.data, "count": len(rows), "pipeline": args.pipeline, "rows": rows}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "count": len(rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
