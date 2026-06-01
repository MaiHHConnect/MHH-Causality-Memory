#!/usr/bin/env python3
"""
CausaMem 做梦脚本
小整理：每天 02:30 — 过滤重要事件
大做梦：每周四 03:00 — 因果串线 + 抽象总结
"""

import sys
import os
import json
import glob
import re
from datetime import datetime, timedelta
from pathlib import Path

# 添加 gbrain 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbrain import put_page_structured

MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.expanduser("~/.openclaw/workspace-main/memory"))
WIKI_DIR = os.environ.get("WIKI_DIR", os.path.expanduser("~/Documents/Obsidian Vault/07_知识库/llm-wiki"))
CAUSAL_ITEM_TEXT_LIMIT = 200


def extract_section_lines(markdown: str, heading: str) -> list[str]:
    """Extract bullet lines from a markdown section."""
    lines = []
    in_section = False
    for raw in markdown.splitlines():
        line = raw.strip()
        heading_match = re.match(r"^#{2,6}\s*(.+?)\s*[:：]?\s*$", line)
        if heading_match:
            in_section = heading_match.group(1).strip() == heading
            continue
        if in_section:
            if not line:
                continue
            item_match = re.match(r"^(?:[-*]|\d+[.)、])\s*(.+)$", line)
            if item_match:
                item = item_match.group(1).strip()
                if item and not item.startswith("（"):
                    lines.append(item[:CAUSAL_ITEM_TEXT_LIMIT])
    return lines


def build_dream_structured(summary: str, date_str: str, dates: list[str]) -> dict:
    five_core_events = extract_section_lines(summary, "时人事因果")
    causal_chains = extract_section_lines(summary, "因果串线")
    future_hints = extract_section_lines(summary, "对未来的暗示")
    relation_findings = extract_section_lines(summary, "关系发现")
    stage_judgment = extract_section_lines(summary, "阶段判断")
    profile_reviews = extract_section_lines(summary, "待确认画像建议")
    source_refs = [
        {"type": "memory_file", "date": d, "path": os.path.join(MEMORY_DIR, f"{d}.md")}
        for d in dates
    ]
    return {
        "decided": "",
        "learned": "\n".join(relation_findings + stage_judgment)[:1000],
        "completed": "",
        "next_steps": "\n".join(future_hints),
        "concepts": ["D5_DREAM", "causal-memory", "dream-consolidation"],
        "cause": "\n".join(causal_chains),
        "effect": "\n".join(future_hints),
        "emotion": "无",
        "summary_struct": {
            "type": "D5_DREAM",
            "date": date_str,
            "period": "过去7天",
            "source_dates": dates,
            "source_refs": source_refs,
            "relation_findings": relation_findings,
            "stage_judgment": stage_judgment,
            "five_core_events": five_core_events,
            "causal_chains": causal_chains,
            "future_hints": future_hints,
            "profile_candidate_review": profile_reviews,
        },
    }


def read_memory_files(dates):
    """读取指定日期的 memory 文件"""
    content = []
    for date in dates:
        path = os.path.join(MEMORY_DIR, f"{date}.md")
        if os.path.exists(path):
            with open(path) as f:
                content.append(f"# {date}\n{f.read()}")
    return "\n\n".join(content)


def run_small_dream():
    """小整理：过滤重要事件，追加到当天日记"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    path = os.path.join(MEMORY_DIR, f"{today}.md")
    if not os.path.exists(path):
        print(f"[dream] No memory file for today ({today}), skipping")
        return
    
    with open(path) as f:
        content = f.read()
    
    # 简单判断是否有重要内容（包含决策/完成/项目关键词）
    keywords = ["决定", "完成", "发布", "修复", "升级", "配置", "重要", "问题", "成果"]
    important = [line for line in content.split("\n") if any(k in line for k in keywords)]
    
    if important:
        output = f"\n## 小整理 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        output += "\n".join(important[:5])  # 最多5条
        with open(path, "a") as f:
            f.write(output)
        print(f"[dream] 小整理完成，追加 {len(important)} 条到 {today}.md")
    else:
        print(f"[dream] 今日无重要事件，跳过")


def run_big_dream():
    """大做梦：因果串线 + 抽象总结"""
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
    
    content = read_memory_files(dates)
    if not content.strip():
        print("[dream] 过去7天无 memory 内容，跳过")
        return
    
    # 生成文件名
    date_str = today.strftime("%Y-%m-%d")
    output_path = os.path.join(WIKI_DIR, "_dream", f"dream-{date_str}.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 调用 AI 生成抽象总结（如果有 API key）
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if api_key:
        summary = generate_dream_summary(content, api_key)
    else:
        summary = generate_fallback_summary(content)
    
    # 写入文件
    source_refs_yaml = "\n".join(
        f"  - type: memory_file\n    date: {d}\n    path: {os.path.join(MEMORY_DIR, f'{d}.md')}"
        for d in dates
    )
    frontmatter = f"""---
title: 浩哥的梦 {date_str}
type: dream
date: {date_str}
period: 过去7天
created: {datetime.now().isoformat()}
source_refs:
{source_refs_yaml}
---

{summary}
"""
    with open(output_path, "w") as f:
        f.write(frontmatter)
    
    print(f"[dream] 大做梦完成，写入 {output_path}")
    
    # 同时写入 gbrain（因果记忆）
    slug = f"dream-{date_str}"
    structured = build_dream_structured(summary, date_str, dates)
    put_page_structured(slug, frontmatter, page_type="dream", title=f"做梦 {date_str}", obs_type="D5_DREAM", structured_override=structured, merge_causal=False)
    print(f"[dream] 已写入 gbrain: {slug}")


def generate_dream_summary(content: str, api_key: str) -> str:
    """调用 AI 生成做梦内容"""
    import requests
    
    prompt = f"""分析过去7天的记忆，生成因果串线和抽象总结。

记忆内容：
{content[:3000]}

请生成以下内容（严格按格式，不要有其他内容）：

## 关系发现
- [人物A] 和 [人物B]：[关系描述]

## 阶段判断
- [项目名]：当前阶段：[判断]

## 时人事因果
- 时：[日期/时间线索]；人：[人物/系统]；事：[做了什么]；因：[为什么做]；果：[结果是什么]

时人事因果是长期记忆核心，只记录有证据的事件；不知道的字段写“待核实”，不要脑补。
做梦层负责整理质量：统一同一概念的不同说法（如 Dreaming/做梦/睡眠记忆整理），但不要编造新事件；删除“OpenClaw memory YYYY-MM-DD”这类纯标题事件；把长段落拆成多个独立事件；合并重复事件；优先保留能回答“什么时候、谁、做了什么、为什么、结果”的事件。
检索层已有向量和文本搜索，不要为了检索制造同义词清单；这里输出干净链条即可。

## 因果串线
- 事件A → 事件B → 事件C

因果串线按时间倒序排列，每条包含日期或时间线索，不要添加“最新/较早/更早”等相对标签；尽量保留全部关键链条；每条不超过 {CAUSAL_ITEM_TEXT_LIMIT} 字；条数不限；保留必要链条结构，不要强行改成 A → B。

## 待确认画像建议
- [候选画像]：[保留/合并/冲突/删除建议]；证据：[用户原句或来源]

画像候选清理规则：画像只是意图/偏好线索，不是主系统；只清理和建议，不要确认成 active 画像；合并重复候选；删除无用户原句证据、从行为/话题推断、从助手建议推断的候选；发现与既有偏好冲突时标记“冲突”，不要覆盖。

## 对未来的暗示
- [可操作的下一步]
"""
    
    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-M2.5", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
            timeout=30
        )
        result = resp.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return text if text else generate_fallback_summary(content)
    except Exception as e:
        print(f"[dream] AI 生成失败: {e}")
        return generate_fallback_summary(content)


def generate_fallback_summary(content: str) -> str:
    """无 API key 时生成简单总结"""
    lines = [l for l in content.split("\n") if l.strip() and l.startswith("#")]
    return f"""## 摘要
过去7天共 {len(lines)} 条记录。
详细内容见 memory/ 目录。

## 因果串线
（需要配置 MINIMAX_API_KEY 才能生成；按时间倒序排列，每条带日期或时间线索，每条200字内，条数不限）

## 时人事因果
（无 API key，未提炼时人事因果事件）

## 待确认画像建议
（无 API key，未清理候选画像）
"""


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "big"
    if mode == "small":
        run_small_dream()
    else:
        run_big_dream()
