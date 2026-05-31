#!/usr/bin/env python3
"""Refine session JSONL files into CausaMem C1 pages.

This is an offline migration/refinement tool. It does not send each event to an
LLM. It reads raw session logs, extracts useful text, groups events by
agent/topic/day, and writes compact C1 summary pages into gbrain.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path


MAX_SNIPPET = 360


def load_gbrain(path):
    spec = importlib.util.spec_from_file_location("gbrain", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load gbrain module: {path}")
    gbrain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gbrain)
    return gbrain


def clean(text):
    text = re.sub(r"\n|\r", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"text", "thinking"}:
                    parts.append(str(item.get("text") or item.get("thinking") or ""))
                elif item_type == "toolCall":
                    parts.append(f"toolCall {item.get('name')} {item.get('arguments')}")
                elif item_type == "toolResult":
                    parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return ""


def day_from(text, fallback="unknown-date"):
    match = re.search(r"(20\d\d-\d\d-\d\d)", text or "")
    return match.group(1) if match else fallback


def parse_line(line):
    try:
        obj = json.loads(line)
    except Exception:
        return None

    ts = str(obj.get("timestamp") or obj.get("ts") or "")
    role = "system"
    text = ""
    if isinstance(obj.get("message"), dict):
        msg = obj["message"]
        role = msg.get("role") or role
        text = text_from_content(msg.get("content"))
    elif obj.get("type") in {"message", "toolResult"}:
        text = text_from_content(obj.get("content"))
    elif obj.get("summary"):
        text = str(obj.get("summary"))
    elif obj.get("payload"):
        text = json.dumps(obj.get("payload"), ensure_ascii=False)[:1200]

    text = clean(text)
    if not text or len(text) < 20:
        return None
    return {
        "timestamp": ts,
        "day": day_from(ts + " " + text),
        "role": role,
        "text": text[:MAX_SNIPPET],
    }


def topic_of(text):
    low = text.lower()
    if any(k.lower() in low for k in ["causamem", "gbrain", "memory", "记忆", "wiki", "dream", "梦境", "bridge", "桥接"]):
        return "memory-system"
    if any(k in text for k in ["日报", "周报", "工作日志", "提醒", "任务", "审批", "cron", "心跳"]):
        return "operations"
    if any(k.lower() in low for k in ["error", "failed", "fix", "bug", "报错", "修复", "启动", "服务"]):
        return "troubleshooting"
    if any(k.lower() in low for k in ["openclaw", "agent", "tool", "hook", "plugin", "插件"]):
        return "agent-runtime"
    if any(k in text for k in ["项目", "客户", "店铺", "订单", "直播", "客服", "电商"]):
        return "business-project"
    return "general"


def agent_from_path(path, agents_dir):
    rel = path.relative_to(agents_dir)
    return rel.parts[0]


def iter_session_files(agents_dir, agent_filter, max_files):
    agents = [agents_dir / agent_filter] if agent_filter else sorted(p for p in agents_dir.iterdir() if p.is_dir())
    for agent_dir in agents:
        sessions = agent_dir / "sessions"
        if not sessions.is_dir():
            continue
        files = []
        for path in sessions.rglob("*"):
            if not path.is_file():
                continue
            name = path.name
            if name.endswith(".jsonl") or ".jsonl." in name or name.endswith(".trajectory.jsonl"):
                files.append((path.stat().st_mtime, path))
        for _, path in sorted(files, reverse=True)[:max_files]:
            yield path


def build_body(agent, topic, day, items):
    lines = []
    for item in items:
        lines.append(f"- {item['timestamp'] or day} [{item['role']}] {item['text']}")
    timeline = "\n".join(lines)
    return f"""# C1 refined session summary

agent_id: {agent}
topic: {topic}
date: {day}
source: session-jsonl-refine
event_count: {len(items)}

## Summary intent
This page condenses raw session JSONL conversation events into C1 memory. Use this for primary judgment; use original session files only for audit evidence.

## Timeline evidence
{timeline}

## Judgment constraints
- This summary belongs only to agent_id={agent}.
- Do not expose it to other agents unless the operator explicitly merges namespaces.
- If details are insufficient, inspect original sessions as R0 evidence.
"""


def safe_put(gbrain, slug, body, retries):
    for attempt in range(retries):
        try:
            gbrain.put_page(slug, body, page_type="refined-c1")
            return True
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt == retries - 1:
                raise
            time.sleep(2 + attempt)
    return False


def main():
    parser = argparse.ArgumentParser(description="Refine session JSONL logs into CausaMem C1 pages.")
    parser.add_argument("--agents-dir", default=os.path.expanduser("~/.openclaw/agents"), help="Directory containing <agent>/sessions/*.jsonl")
    parser.add_argument("--gbrain", default=str(Path(__file__).with_name("gbrain.py")), help="Path to gbrain.py")
    parser.add_argument("--agent", help="Only refine one agent namespace")
    parser.add_argument("--max-files", type=int, default=10000, help="Maximum files per agent")
    parser.add_argument("--max-lines", type=int, default=10000, help="Maximum lines per session file")
    parser.add_argument("--max-items-per-bucket", type=int, default=60, help="Maximum events kept in each summary page")
    parser.add_argument("--min-general-items", type=int, default=3, help="Skip general buckets below this event count")
    parser.add_argument("--retries", type=int, default=12, help="SQLite locked retry count")
    parser.add_argument("--dry-run", action="store_true", help="Scan and report without writing pages")
    args = parser.parse_args()

    agents_dir = Path(args.agents_dir).expanduser().resolve()
    if not agents_dir.is_dir():
        raise SystemExit(f"agents dir not found: {agents_dir}")

    buckets = defaultdict(list)
    files_scanned = 0
    events_seen = 0
    for path in iter_session_files(agents_dir, args.agent, args.max_files):
        agent = agent_from_path(path, agents_dir)
        files_scanned += 1
        try:
            with path.open(encoding="utf-8", errors="ignore") as fh:
                for index, line in enumerate(fh):
                    if index >= args.max_lines:
                        break
                    event = parse_line(line)
                    if not event:
                        continue
                    buckets[(agent, topic_of(event["text"]), event["day"])].append(event)
                    events_seen += 1
        except OSError:
            continue

    written = 0
    if not args.dry_run:
        gbrain = load_gbrain(args.gbrain)
        for (agent, topic, day), items in sorted(buckets.items()):
            if len(items) < args.min_general_items and topic == "general":
                continue
            digest = hashlib.sha1(f"{agent}|{topic}|{day}".encode()).hexdigest()[:12]
            slug = f"refined-session-{agent}-{topic}-{day}-{digest}".replace("/", "-")
            body = build_body(agent, topic, day, items[:args.max_items_per_bucket])
            if safe_put(gbrain, slug, body, args.retries):
                written += 1

    print(f"session_files_scanned: {files_scanned}")
    print(f"events_seen: {events_seen}")
    print(f"buckets: {len(buckets)}")
    print(f"refined_c1_written: {written}")
    if args.dry_run:
        print("dry_run: true")


if __name__ == "__main__":
    main()
