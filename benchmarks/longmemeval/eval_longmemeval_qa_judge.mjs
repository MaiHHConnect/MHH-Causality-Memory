#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}
function numArg(name, fallback) {
  const v = arg(name, undefined);
  return v == null ? fallback : Number(v);
}

const hypPath = arg('--hyp', 'benchmarks/longmemeval/results/s_qa_top5.jsonl');
const refPath = arg('--ref', 'benchmarks/longmemeval/data/longmemeval_s_cleaned.json');
const outPath = arg('--out', 'benchmarks/longmemeval/results/s_qa_top5_judge.jsonl');
const model = arg('--model', 'minimax/MiniMax-M2.7-highspeed');
const provider = arg('--provider', 'openclaw-cli');
const apiBaseUrl = arg('--api-base-url', process.env.BUY_API_BASE_URL || process.env.OPENAI_BASE_URL || 'https://www.buy-api.com/v1');
const limit = numArg('--limit', 0);
const offset = numArg('--offset', 0);
const resume = !args.includes('--no-resume');
const includeAbstention = args.includes('--include-abstention');

function buildPrompt(ref, hypothesis) {
  return `You are evaluating a QA system.\n\nQuestion:\n${ref.question}\n\nReference answer:\n${String(ref.answer)}\n\nModel answer:\n${String(hypothesis || '')}\n\nDecide whether the model answer is semantically correct. It is correct if it contains the same essential information as the reference answer. Allow paraphrases, extra harmless context, equivalent dates, equivalent numbers, and minor wording differences. Mark incorrect if the answer contradicts the reference, omits the key fact, or says the information is unavailable when the reference has an answer.\n\nReturn only JSON:\n{"verdict":"correct or incorrect","score":1,"reason":"brief explanation"}`;
}
function parseJudge(text) {
  const cleaned = String(text || '').replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```$/i, '').trim();
  try { return JSON.parse(cleaned); } catch {}
  const m = cleaned.match(/\{[\s\S]*\}/);
  if (!m) throw new Error(`failed to parse judge JSON: ${cleaned.slice(0, 500)}`);
  return JSON.parse(m[0]);
}
function callOpenClaw(prompt) {
  const res = spawnSync('openclaw', ['infer', 'model', 'run', '--gateway', '--model', model, '--prompt', prompt, '--json'], {
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
    timeout: 120000,
  });
  if (res.status !== 0) throw new Error(`openclaw exited ${res.status}: ${(res.stderr || res.stdout || '').slice(0, 1000)}`);
  const parsed = JSON.parse(res.stdout);
  const text = parsed?.outputs?.[0]?.text;
  if (!text) throw new Error(`empty model output: ${res.stdout.slice(0, 1000)}`);
  return text.trim();
}
function callOpenAICompatible(prompt) {
  const key = process.env.BUY_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) throw new Error('missing BUY_API_KEY or OPENAI_API_KEY for openai-compatible provider');
  const url = `${apiBaseUrl.replace(/\/+$/, '')}/chat/completions`;
  const requestId = `longmemeval-judge-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const res = spawnSync('curl', [
    '-sS', '--fail-with-body',
    '-X', 'POST', url,
    '-H', `Authorization: Bearer ${key}`,
    '-H', 'Content-Type: application/json',
    '-H', `X-Request-ID: ${requestId}`,
    '--data', JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0,
      stream: false,
    }),
  ], {
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
    timeout: 180000,
  });
  if (res.status !== 0) throw new Error(`openai-compatible exited ${res.status}: ${(res.stderr || res.stdout || '').slice(0, 1000)}`);
  const parsed = JSON.parse(res.stdout);
  const text = parsed?.choices?.[0]?.message?.content || parsed?.choices?.[0]?.text;
  if (!text) throw new Error(`empty model output: ${res.stdout.slice(0, 1000)}`);
  return String(text).trim();
}
function judge(ref, hypothesis) {
  if (provider === 'mock') {
    const ok = String(hypothesis || '').toLowerCase().includes(String(ref.answer || '').toLowerCase());
    return { verdict: ok ? 'correct' : 'incorrect', score: ok ? 1 : 0, reason: 'mock substring judge', raw_judge: '' };
  }
  let raw = '';
  if (provider === 'openclaw-cli') raw = callOpenClaw(buildPrompt(ref, hypothesis));
  else if (provider === 'openai-compatible') raw = callOpenAICompatible(buildPrompt(ref, hypothesis));
  else throw new Error(`unsupported provider: ${provider}`);
  const parsed = parseJudge(raw);
  const verdict = String(parsed.verdict || '').toLowerCase().includes('correct') && !String(parsed.verdict || '').toLowerCase().includes('incorrect') ? 'correct' : 'incorrect';
  const score = Number(parsed.score ?? (verdict === 'correct' ? 1 : 0)) ? 1 : 0;
  return { verdict, score, reason: String(parsed.reason || ''), raw_judge: raw };
}

const refs = new Map(JSON.parse(fs.readFileSync(refPath, 'utf8')).map(x => [x.question_id, x]));
let rows = fs.readFileSync(hypPath, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line)).map(h => ({ hyp: h, ref: refs.get(h.question_id) })).filter(x => x.ref);
if (!includeAbstention) rows = rows.filter(x => !String(x.ref.question_id || '').endsWith('_abs'));
rows = rows.slice(offset, limit > 0 ? offset + limit : undefined);
fs.mkdirSync(path.dirname(outPath), { recursive: true });

const done = new Set();
if (resume && fs.existsSync(outPath)) {
  for (const line of fs.readFileSync(outPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try { done.add(JSON.parse(line).question_id); } catch {}
  }
}
if (!resume) fs.writeFileSync(outPath, '');

let completed = 0, skipped = 0, failed = 0, correct = 0;
const byType = new Map();
for (const row of rows) {
  if (done.has(row.ref.question_id)) { skipped += 1; continue; }
  try {
    const j = judge(row.ref, row.hyp.hypothesis);
    const out = { question_id: row.ref.question_id, question_type: row.ref.question_type, question: row.ref.question, answer: row.ref.answer, hypothesis: row.hyp.hypothesis, judge_model: model, provider, verdict: j.verdict, score: j.score, reason: j.reason, raw_judge: j.raw_judge };
    fs.appendFileSync(outPath, JSON.stringify(out) + '\n');
    completed += 1;
    correct += j.score ? 1 : 0;
    const type = row.ref.question_type || 'unknown';
    if (!byType.has(type)) byType.set(type, { total: 0, correct: 0 });
    byType.get(type).total += 1;
    byType.get(type).correct += j.score ? 1 : 0;
    console.log(JSON.stringify({ ok: true, question_id: row.ref.question_id, completed, total: rows.length }));
  } catch (err) {
    failed += 1;
    console.error(JSON.stringify({ ok: false, question_id: row.ref.question_id, error: String(err.message || err).slice(0, 1000) }));
  }
}
const by_type = {};
for (const [type, v] of [...byType.entries()].sort()) by_type[type] = { ...v, accuracy: v.total ? Number((v.correct / v.total).toFixed(4)) : 0 };
console.log(JSON.stringify({ metric: 'llm-judge', model, hyp: hypPath, ref: refPath, out: outPath, selected: rows.length, completed, skipped, failed, correct, accuracy: completed ? Number((correct / completed).toFixed(4)) : 0, by_type }, null, 2));
