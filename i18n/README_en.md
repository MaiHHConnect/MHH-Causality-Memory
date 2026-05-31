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

CausaMem uses `R0 -> C1 -> I2` as its cognitive backbone. Expanded into the runtime system, this becomes an 8-layer process:

```text
R0 Reality Evidence
  -> F1 Atomic Factlets
  -> S2 Refined Summaries
  -> P3 Profiles and Scenes
  -> K4 Wiki Knowledge
  -> D5 Dream Consolidation
  -> C6 Causal Chains
  -> I7 Intuition Injection
```

The system first preserves evidence, then refines facts, summaries, profiles, Wiki knowledge, and dream consolidation, then links causal chains and injects intuition anchors before judgment.

Expanded into the actual runtime system, CausaMem is an 8-layer cognition + intuition + causal memory system:

Design philosophy: an LLM can be treated as something with intelligence, but an Agent does not automatically have complete cognition. Humans are similar: someone can be very capable in one domain, such as games, while still having weak real-world judgment in another. Agents have model capability, but they still need long-term cognitive structure. CausaMem fills that gap by turning long-running experience, project facts, rules, and historical decisions into judgment-ready memory.

Once cognition is built, the Agent also needs something like human intuition. Human intuition often comes from the subconscious; people do not always know which past experiences their subconscious used. CausaMem treats intuition in the same way: before judgment, it embeds refined facts, risks, tendencies, and next-step suggestions into context. The Agent does not need to know exactly which part of a multi-million-character history was activated, but it is anchored by the distilled essence of that history.

Finally, long-term memory cannot remain a pile of facts. It needs causal chains. CausaMem compresses conversations, execution traces, project experience, and historical decisions into durable life/project essence, then tracks why something happened, what it caused, and whether it is still valid. This moves the Agent from remembering more to judging better.

- **Cognition** turns raw conversations, execution traces, and project facts into judgment-ready structure: facts, rules, scenes, profiles, and historical decisions.
- **Intuition** compresses the most important facts, risks, and next-step tendencies into a cognitive anchor before judgment, so the agent starts from the right direction.
- **Causality** is derived from evidence, historical decisions, task outcomes, and conflict changes to answer why something happened, what it caused, and whether it is still valid.

| Layer | Name | Role |
|-------|------|------|
| R0 | Reality Evidence | Raw sessions, captures, logs, and events for audit and evidence fallback |
| F1 | Atomic Factlets | Answerable, retrievable, evidence-backed `factlet-c1` facts extracted from source text |
| S2 | Refined Summaries | Topic/date/agent-level C1 summaries from long conversations |
| P3 | Profiles and Scenes | Stable preferences, people, project scenes, and long-running state |
| K4 | Wiki Knowledge | Curated and semi-curated durable knowledge backbone |
| D5 | Dream Consolidation | Asynchronous consolidation that turns scattered experience into higher-level memory |
| C6 | Causal Chains | Causes, effects, conflicts, evolution, and supersession relationships |
| I7 | Intuition Injection | Judgment-time tendencies, next-step suggestions, and cognitive anchors |

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

On the long-running `ai666` OpenClaw container, the `refined-c1` judgment layer performed as follows:

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

### Refined factlet QA test (ai666 / 30 cases)

On the same long-running `ai666` OpenClaw container, 30 real facts were sampled from the formal `factlet-c1` refined memory layer. The test retrieves the CausaMem memory page first, then gives the full `Fact/Evidence` context to the model for answering.

Underlying data scope: roughly 200k historical session lines / multi-million-character long-running interaction history, refined by LLM extraction and deterministic evidence gates into `factlet-c1`.

```text
Source: factlet-c1
Cases: 30
Retrieval hit: 30/30
Answer pass: 29/30
Pass rate: 96.7%
```

This measures answerability after refinement, not just retrieval hit rate. The only failed case still retrieved the correct factlet, but the answer blended several related memories instead of precisely restating one time-specific fact. This is answer over-generalization, not retrieval failure.

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
