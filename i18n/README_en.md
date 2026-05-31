# CausaMem - Causal Memory and Cognitive Anchoring for AI Agents

> Permanent causal memory for long-running AI agents.
> Before an agent reasons, CausaMem anchors it with facts, rules, decisions, causal chains, and execution state.

[Back to main README](../README.md)

## What It Is

CausaMem is a causal memory system for AI agents that operate across long-running projects, sessions, tools, and decisions.

Most memory systems retrieve similar text after a question is asked. CausaMem is stricter: it captures raw reality, extracts candidate memories, gates what can enter long-term memory, and injects a cognitive anchor before the agent reasons.

The result is not just semantic search. It is memory-grounded reasoning.

## Core Idea

Memory is not a warehouse. Memory is a causal web.

```text
cause -> effect -> next effect -> decision -> consequence
```

When an agent touches one node, CausaMem can trace what happened, why it happened, what decision was made, what it caused, whether it is still valid, and what the agent should know before answering.

## Cognitive Anchoring

CausaMem uses a three-layer anchoring model:

```text
R0 Reality Evidence Layer
  Raw events, execution traces, Beads task state, observed facts

C1 Cognitive Structure Layer
  Memory candidates, pages, causal edges, scenes, profiles, decisions

I2 Intuition Injection Layer
  A compact cognitive anchor injected before the agent reasons
```

The anchor contains facts, rules, historical decisions, causal chains, execution state, and judgment constraints.

## Recall Pipeline

CausaMem combines multiple retrieval signals instead of relying on vector similarity alone:

```text
keyword search
+ FTS
+ vector search
+ lexical fallback
+ causal edges
+ recency
-> RRF ranking
-> MMR deduplication
-> causal activation
-> cognitive anchor
```

Current internal project-memory regression set:

```text
50 real project questions
hit_rate: 1.000
MRR: 0.974
```

This is a regression set for CausaMem's own project memory, not a public benchmark.

Real long-running memory benchmark from the `ai666` OpenClaw container:

```text
real evaluable pages: 3265
sample size: 2000
overall hit@1: 0.5465
overall hit@3: 0.6215
overall hit@6: 0.6555
overall MRR:   0.5888
```

The overall score includes noisy R0 raw session logs, retired Hy-Memory L0 records, and raw OpenClaw captures. The C1 judgment layer is the primary usage signal:

```text
refined-c1 n=872
hit@1: 0.9495
hit@3: 0.9817
hit@6: 0.9943
MRR:   0.9676
```

Source-level snapshot:

| Source | n | hit@1 | hit@3 | hit@6 | MRR |
|---|---:|---:|---:|---:|---:|
| `refined-c1` | 872 | 0.9495 | 0.9817 | 0.9943 | 0.9676 |
| `memos-local` | 217 | 0.7281 | 0.9585 | 0.9770 | 0.8445 |
| `dream-c1` | 19 | 0.5789 | 0.7368 | 0.8947 | 0.6807 |
| `wiki-c1` | 205 | 0.3512 | 0.5512 | 0.6829 | 0.4707 |
| `session-file` | 518 | 0.0058 | 0.0328 | 0.0695 | 0.0255 |

Conclusion: the refined C1 layer is stable for primary judgment. R0 raw logs are better treated as audit evidence, not as the main recall-quality signal.

## Controlled Memory Writes

CausaMem does not let an LLM write directly into long-term memory.

```text
capture
-> extract/import candidates
-> model gate
-> deterministic CausaMem gate
-> commit approved memories only
```

The model proposes JSON decisions. CausaMem verifies them.

The deterministic gate checks that evidence appears in the source candidate, Profile confidence is at least 0.75, temporary status cannot become long-term Profile, Profile type/key is allowlisted, and conflicts become conflict records instead of overwrites.

## OpenClaw Integration

CausaMem integrates with OpenClaw through two hooks:

```text
before_prompt_build
  -> build and inject cognitive anchor before reasoning

agent_end
  -> capture conversation
  -> extract candidate memories
  -> run model gate
  -> apply deterministic gate
  -> commit approved memories
```

This makes memory part of the reasoning loop, not an afterthought.

## Beads Integration

CausaMem can use [Beads](https://github.com/gastownhall/beads) as an execution-tracking reality source. Beads provides task state, dependencies, audit trail, ready queue, and execution graph context.

CausaMem treats Beads as R0 reality evidence. Beads does not replace CausaMem and does not become the primary memory system.

## Why Not Plain Vector Memory

| Capability | Plain Vector Memory | CausaMem |
|---|---:|---:|
| Semantic recall | Yes | Yes |
| Exact lexical fallback | Partial | Yes |
| Causal chain tracing | No | Yes |
| Execution-state grounding | No | Yes |
| Pre-reasoning context injection | Rare | Yes |
| Profile write gate | No | Yes |
| Conflict handling | No | Yes |
| Long-running project memory | Weak | Strong |

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
/usr/bin/python3 scripts/gbrain/gbrain.py init
/usr/bin/python3 scripts/gbrain/gbrain.py doctor
```

Build a cognitive anchor:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py anchor "What should the agent know before answering?"
```

Run recall regression:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py eval eval/gbrain_eval.jsonl
```

## Session Memory Refiner

`scripts/gbrain/refine_sessions.py` turns long-running session JSONL logs into compact C1 memory pages.

It does not send every message to an LLM. The tool runs locally:

```text
session JSONL -> extract useful text -> isolate by agent -> bucket by topic/date -> refined-c1 -> CausaMem
```

Example:

```bash
python3 scripts/gbrain/refine_sessions.py \
  --agents-dir ~/.openclaw/agents \
  --gbrain scripts/gbrain/gbrain.py \
  --agent main \
  --max-files 10000 \
  --max-lines 10000
```

Useful flags:

| Flag | Description |
|---|---|
| `--agents-dir` | Directory containing `<agent>/sessions/*.jsonl` |
| `--agent` | Refine one agent namespace only |
| `--max-files` | Maximum session files per agent |
| `--max-lines` | Maximum lines per session file |
| `--dry-run` | Scan and report without writing pages |

The generated pages use slugs like `refined-session-main-memory-system-2026-05-31-xxxx` and include `agent_id`, `topic`, `date`, and judgment constraints. This is the recommended first pass for turning R0 raw conversations into the C1 judgment layer.

## Security

Do not commit API keys, tokens, local databases, Beads runtime data, or credentials. Use environment variables for `SILICONFLOW_API_KEY` and `MINIMAX_API_KEY`.

## License

CC BY-NC 4.0. Commercial use requires explicit permission.

Contact: 3871169@qq.com
