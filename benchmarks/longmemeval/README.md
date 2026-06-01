# LongMemEval Benchmark

Local, reproducible LongMemEval retrieval checks for CausaMem-style memory retrieval.

This directory does not vendor the LongMemEval dataset. Download the public cleaned data locally before running benchmarks.

## Dataset

Source: `xiaowu0162/longmemeval-cleaned`

Primary file used here:

- `longmemeval_s_cleaned.json`
- 500 total questions
- 470 answerable questions
- 30 abstention/no-answer questions skipped for retrieval-hit metrics

Download with:

```bash
curl -L -C - \
  -o benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  https://hf-mirror.com/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json
```

Optional oracle file:

```bash
curl -L -C - \
  -o benchmarks/longmemeval/data/longmemeval_oracle.json \
  https://hf-mirror.com/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_oracle.json
```

## Run

```bash
node benchmarks/longmemeval/run_longmemeval_retrieval.mjs \
  --data benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_retrieval_results.json
```

Or with Python:

```bash
/usr/bin/python3 benchmarks/longmemeval/run_longmemeval_retrieval.py \
  --data benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_retrieval_results.json
```

The runners are dependency-free and use BM25-style lexical scoring over each session. They measure whether a session containing the answer evidence is retrieved into top-k context.

## Current Result

Run date: 2026-05-31

Dataset: `longmemeval_s_cleaned.json`

| Metric | Score |
|--------|------:|
| cases | 470 |
| hit@1 | 0.8660 |
| hit@3 | 0.9404 |
| hit@5 | 0.9681 |
| hit@10 | 0.9809 |
| MRR | 0.9072 |

By question type:

| Type | n | hit@1 | hit@3 | hit@5 | hit@10 | MRR |
|------|--:|------:|------:|------:|-------:|----:|
| knowledge-update | 72 | 0.9444 | 0.9861 | 1.0000 | 1.0000 | 0.9688 |
| multi-session | 121 | 0.8760 | 0.9421 | 0.9587 | 0.9835 | 0.9132 |
| single-session-assistant | 56 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| single-session-preference | 30 | 0.3667 | 0.7000 | 0.8667 | 0.8667 | 0.5588 |
| single-session-user | 64 | 0.9375 | 0.9688 | 1.0000 | 1.0000 | 0.9602 |
| temporal-reasoning | 127 | 0.8346 | 0.9291 | 0.9528 | 0.9764 | 0.8812 |

## Notes

- `longmemeval_oracle.json` is useful for plumbing checks only. It contains only the evidence sessions, so retrieval scores can be trivially perfect and should not be used as the headline benchmark.
- This retrieval runner does not evaluate answer generation quality. Use the official LongMemEval QA evaluation flow for final answer-quality reporting.
- The downloaded dataset, generated results, and upstream clone are ignored by Git to avoid committing large public data or nested repository metadata.

## QA Generation

Generate answers with BM25 top-k sessions plus the local OpenClaw gateway:

```bash
node benchmarks/longmemeval/run_longmemeval_qa.mjs \
  --data benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_qa_top5.jsonl \
  --topk 5
```

Useful options:

- `--provider mock|openclaw-cli|openai-compatible`
- `--model <provider/model>`
- `--api-base-url <url>` for OpenAI-compatible providers; default reads `BUY_API_BASE_URL`/`OPENAI_BASE_URL` or `https://api.buy-api.com/v1`
- `--limit N --offset N`
- `--shard-count N --shard-index I`
- `--session-char-limit N` truncates assistant turns in prompt context; user turns stay intact
- `--prompt-mode generic|task-aware`
- `--context-mode bm25|causamem|bm25+causamem|real_causamem|bm25+real_causamem`
- `--gbrain-cache-dir <dir>` for per-question real CausaMem DBs
- `--include-abstention`
- default resume is enabled; use `--no-resume` only for a fresh output file

Task-aware prompting keeps the same retrieved evidence but adds instructions for LongMemEval task types such as temporal reasoning, knowledge updates, multi-session aggregation, and user preferences. Keep task-aware outputs in separate files from baseline outputs.

The QA prompt places the question before long memory context. With long contexts, placing the question only at the end can cause repeated or stale answers on some OpenAI-compatible gateways.

CausaMem context mode turns the retrieved sessions into a compact dated causal memory block ordered newest to oldest. It is useful for testing whether causal-style context helps state updates, temporal reasoning, and multi-session aggregation:

```bash
node benchmarks/longmemeval/run_longmemeval_qa.mjs \
  --data benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_qa_top5_causamem.jsonl \
  --topk 5 \
  --context-mode causamem \
  --prompt-mode task-aware
```

`bm25+causamem` includes both the compact causal memory block and the raw retrieved chats. `causamem` includes only the compact dated causal memory block.

Real CausaMem mode uses actual `gbrain.py anchor --json` output. Prepare one isolated DB per question before running it:

```bash
/usr/bin/python3 benchmarks/longmemeval/prepare_longmemeval_gbrain.py \
  --data benchmarks/longmemeval/results/target_30_tmk.json \
  --out-dir benchmarks/longmemeval/results/gbrain_cache_target_30 \
  --gbrain scripts/gbrain/gbrain.py \
  --force
```

Then run QA with the cache directory:

```bash
node benchmarks/longmemeval/run_longmemeval_qa.mjs \
  --data benchmarks/longmemeval/results/target_30_tmk.json \
  --out benchmarks/longmemeval/results/target_30_bm25_real_causamem_taskaware.jsonl \
  --topk 5 \
  --context-mode bm25+real_causamem \
  --gbrain-cache-dir benchmarks/longmemeval/results/gbrain_cache_target_30 \
  --prompt-mode task-aware \
  --no-resume
```

`real_causamem` refuses to use the default machine DB. Pass `--gbrain-cache-dir` or `--gbrain-db` explicitly to avoid cross-case contamination.

For Buy-API/OpenAI-compatible runs, set the key in the environment instead of writing it into result files or commands:

```bash
export BUY_API_KEY="sk-..."
export BUY_API_BASE_URL="https://api.buy-api.com/v1"
node benchmarks/longmemeval/run_longmemeval_qa.mjs \
  --data benchmarks/longmemeval/results/target_30_tmk.json \
  --out benchmarks/longmemeval/results/target_30_bm25_gpt55.jsonl \
  --provider openai-compatible \
  --model gpt-5.5 \
  --context-mode bm25 \
  --prompt-mode task-aware \
  --no-resume
```

## QA Evaluation

Fast lexical sanity check:

```bash
node benchmarks/longmemeval/eval_longmemeval_qa_light.mjs \
  --hyp benchmarks/longmemeval/results/s_qa_top5.jsonl \
  --ref benchmarks/longmemeval/data/longmemeval_s_cleaned.json
```

LLM judge check using OpenClaw:

```bash
node benchmarks/longmemeval/eval_longmemeval_qa_judge.mjs \
  --hyp benchmarks/longmemeval/results/s_qa_top5.jsonl \
  --ref benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_qa_top5_judge.jsonl
```

Use `--provider mock --limit 5 --no-resume` for a local smoke test without model calls.

## Error Analysis

Classify light-eval failures:

```bash
node benchmarks/longmemeval/analyze_longmemeval_qa_errors.mjs \
  --hyp benchmarks/longmemeval/results/s_qa_top5.jsonl \
  --ref benchmarks/longmemeval/data/longmemeval_s_cleaned.json \
  --out benchmarks/longmemeval/results/s_qa_error_analysis.json
```

The analyzer is heuristic and dependency-free. It separates likely substring false negatives, retrieval misses, state-update errors, aggregation errors, temporal errors, preference-prompt errors, and generation errors.

Compare two QA runs by question id:

```bash
node benchmarks/longmemeval/compare_longmemeval_runs.mjs \
  --base benchmarks/longmemeval/results/target_30_bm25_gpt55.jsonl \
  --test benchmarks/longmemeval/results/target_30_bm25_real_causamem_gpt55.jsonl \
  --ref benchmarks/longmemeval/results/target_30_tmk.json \
  --out benchmarks/longmemeval/results/target_30_compare_bm25_vs_bm25_real.json
```

## Caveats

- Retrieval metrics measure evidence-session recall only, not final answer quality.
- `eval_longmemeval_qa_light.mjs` is a strict normalized substring sanity check and can undercount paraphrases, equivalent dates/numbers, preference answers, and temporal off-by-one cases.
- LLM judge results should be reported with model name, prompt version, and by-type breakdown.
- Do not compare light-eval accuracy directly against published LongMemEval judge results.
