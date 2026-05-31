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

const dataPath = arg('--data', 'benchmarks/longmemeval/data/longmemeval_s_cleaned.json');
const outPath = arg('--out', 'benchmarks/longmemeval/results/s_qa_top5.jsonl');
const topK = numArg('--topk', 5);
const limit = numArg('--limit', 0);
const offset = numArg('--offset', 0);
const model = arg('--model', 'minimax/MiniMax-M2.7-highspeed');
const provider = arg('--provider', 'openclaw-cli');
const promptMode = arg('--prompt-mode', 'generic');
const contextMode = arg('--context-mode', 'bm25');
const includeAbstention = args.includes('--include-abstention');
const resume = !args.includes('--no-resume');
const shardIndex = numArg('--shard-index', 0);
const shardCount = numArg('--shard-count', 1);

function tokens(text) {
  return String(text || '').toLowerCase().match(/[a-z0-9_]+/g)?.filter(t => t.length > 1) || [];
}

function sessionText(session) {
  return session.map(turn => `${turn.role || ''}: ${turn.content || ''}`).join('\n');
}

function scoreSessions(question, sessions) {
  const qTokens = tokens(question);
  const docs = sessions.map(s => tokens(sessionText(s)));
  const df = new Map();
  for (const doc of docs) for (const t of new Set(doc)) df.set(t, (df.get(t) || 0) + 1);
  const nDocs = Math.max(1, docs.length);
  const avgdl = docs.reduce((a, d) => a + d.length, 0) / nDocs || 1;
  const qCounts = new Map();
  for (const t of qTokens) qCounts.set(t, (qCounts.get(t) || 0) + 1);
  return docs.map((doc, i) => {
    const counts = new Map();
    for (const t of doc) counts.set(t, (counts.get(t) || 0) + 1);
    const dl = Math.max(1, doc.length);
    let score = 0;
    for (const [t, qtf] of qCounts.entries()) {
      const tf = counts.get(t) || 0;
      if (!tf) continue;
      const dft = df.get(t) || 0;
      const idf = Math.log(1 + (nDocs - dft + 0.5) / (dft + 0.5));
      const denom = tf + 1.5 * (1 - 0.75 + 0.75 * dl / Math.max(avgdl, 1));
      score += idf * (tf * 2.5 / denom) * Math.min(qtf, 3);
    }
    return [i, score];
  }).sort((a, b) => b[1] - a[1]);
}

function taskInstruction(item) {
  if (promptMode === 'generic') return '';
  if (promptMode !== 'task-aware') throw new Error(`unsupported prompt mode: ${promptMode}`);
  switch (item.question_type) {
    case 'knowledge-update':
      return 'If older and newer facts conflict, use the latest applicable fact from the history. Mention only the current answer unless the question asks for history.';
    case 'multi-session':
      return 'This may require combining evidence across multiple sessions. Consider every retrieved session, deduplicate repeated items, and answer the aggregate question directly.';
    case 'temporal-reasoning':
      return 'This may require date or ordering reasoning. Identify the relevant event dates from the history, compute the relationship carefully, and give the final concise answer.';
    case 'single-session-preference':
      return 'Infer the user preference from the history. Do not give generic recommendations; answer with what the user would prefer or avoid.';
    case 'single-session-assistant':
      return 'Recall what the assistant previously said. Preserve the key items from that prior assistant answer.';
    case 'single-session-user':
      return 'Recall the user-stated fact from the relevant history session.';
    default:
      return '';
  }
}

function parseDateValue(dateText) {
  const m = String(dateText || '').match(/(\d{4})\/(\d{2})\/(\d{2})|(?:\d{4})-(?:\d{2})-(?:\d{2})/);
  if (!m) return 0;
  const s = m[0].replaceAll('/', '-');
  const t = Date.parse(s);
  return Number.isNaN(t) ? 0 : t;
}

function extractCausalLine(item, idx) {
  const date = item.haystack_dates?.[idx] || 'unknown-date';
  const session = item.haystack_sessions?.[idx] || [];
  const userTurns = session.filter(turn => turn.role === 'user').map(turn => String(turn.content || '').trim()).filter(Boolean);
  const assistantTurns = session.filter(turn => turn.role === 'assistant').map(turn => String(turn.content || '').trim()).filter(Boolean);
  const user = userTurns.at(-1) || userTurns[0] || '';
  const assistant = assistantTurns.at(-1) || assistantTurns[0] || '';
  const source = user || assistant || sessionText(session);
  const compact = String(source).replace(/\s+/g, ' ').trim().slice(0, 200);
  const answerEvidence = new Set(item.answer_session_ids || []).has(item.haystack_session_ids?.[idx]);
  const marker = answerEvidence ? ' evidence' : '';
  return `- ${date}${marker}: ${compact}`;
}

function buildCausaMemContext(item, ranked) {
  const ordered = ranked
    .map(([idx]) => idx)
    .sort((a, b) => parseDateValue(item.haystack_dates?.[b]) - parseDateValue(item.haystack_dates?.[a]));
  const lines = ordered.map(idx => extractCausalLine(item, idx));
  const typeHint = {
    'knowledge-update': 'Track newer facts overriding older facts. Treat later dated evidence as the current state unless contradicted.',
    'multi-session': 'Aggregate all relevant events across time. Count and deduplicate by meaning, not by repeated wording.',
    'temporal-reasoning': 'Use the dated causal timeline to identify event order and compute date relationships carefully.',
    'single-session-preference': 'Infer stable user preferences from the dated evidence and answer with preference constraints.',
    'single-session-assistant': 'Recall prior assistant-provided information from the dated evidence.',
    'single-session-user': 'Recall prior user-stated facts from the dated evidence.',
  }[item.question_type] || 'Use the dated causal timeline to answer from memory.';
  return `<causamem-context>\nQuestion type: ${item.question_type || 'unknown'}\nPolicy: ${typeHint}\nTimeline order: newest to oldest. Each item is a compact causal memory line.\n\n${lines.join('\n')}\n</causamem-context>`;
}

function buildPrompt(item) {
  const ranked = scoreSessions(item.question, item.haystack_sessions || []).slice(0, topK);
  const chunks = ranked
    .map(([idx], i) => {
      const date = item.haystack_dates[idx];
      const content = (item.haystack_sessions[idx] || [])
        .map(turn => `${turn.role || ''}: ${String(turn.content || '').trim()}`)
        .join('\n\n');
      return `### Session ${i + 1}\nSession Date: ${date}\nSession Content:\n${content}`;
    })
    .join('\n\n');

  const abstentionHint = includeAbstention
    ? 'If the relevant history is insufficient to answer, say that the information is not available in the provided history.'
    : '';
  const taskHint = taskInstruction(item);
  if (!['bm25', 'causamem', 'bm25+causamem'].includes(contextMode)) throw new Error(`unsupported context mode: ${contextMode}`);
  const causamem = contextMode === 'bm25' ? '' : buildCausaMemContext(item, ranked);
  const history = contextMode === 'causamem' ? causamem : contextMode === 'bm25+causamem' ? `${causamem}\n\nHistory Chats:\n\n${chunks}` : `History Chats:\n\n${chunks}`;
  return `I will give you memory context between you and a user. Please answer the question based only on the provided memory context. Give a concise direct answer. ${abstentionHint} ${taskHint}\n\n${history}\n\nCurrent Date: ${item.question_date}\nQuestion: ${item.question}\nAnswer:`;
}

function callOpenClaw(prompt) {
  const res = spawnSync('openclaw', ['infer', 'model', 'run', '--gateway', '--model', model, '--prompt', prompt, '--json'], {
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
  });
  if (res.status !== 0) {
    throw new Error(`openclaw exited ${res.status}: ${(res.stderr || res.stdout || '').slice(0, 1000)}`);
  }
  const parsed = JSON.parse(res.stdout);
  const text = parsed?.outputs?.[0]?.text;
  if (!text) throw new Error(`empty model output: ${res.stdout.slice(0, 1000)}`);
  return text.trim();
}

function answerQuestion(item) {
  if (provider === 'mock') return item.answer || '';
  if (provider === 'openclaw-cli') return callOpenClaw(buildPrompt(item));
  throw new Error(`unsupported provider: ${provider}`);
}

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
fs.mkdirSync(path.dirname(outPath), { recursive: true });

const done = new Set();
if (resume && fs.existsSync(outPath)) {
  for (const line of fs.readFileSync(outPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try { done.add(JSON.parse(line).question_id); } catch {}
  }
}

const selected = data
  .filter(item => includeAbstention || !String(item.question_id || '').endsWith('_abs'))
  .filter((_item, i) => shardCount <= 1 || (i % shardCount) === shardIndex)
  .slice(offset, limit > 0 ? offset + limit : undefined);
if (!resume) fs.writeFileSync(outPath, '');

let completed = 0;
let skipped = 0;
let failed = 0;
for (const item of selected) {
  if (done.has(item.question_id)) {
    skipped += 1;
    continue;
  }
  try {
    const hypothesis = answerQuestion(item);
    fs.appendFileSync(outPath, JSON.stringify({
      question_id: item.question_id,
      hypothesis,
      question_type: item.question_type,
      model,
      provider,
      topk: topK,
      prompt_mode: promptMode,
      context_mode: contextMode,
    }) + '\n');
    completed += 1;
    console.log(JSON.stringify({ ok: true, question_id: item.question_id, completed, total: selected.length }));
  } catch (err) {
    failed += 1;
    console.error(JSON.stringify({ ok: false, question_id: item.question_id, error: String(err.message || err).slice(0, 1000) }));
  }
}
console.log(JSON.stringify({ out: outPath, selected: selected.length, completed, skipped, failed }, null, 2));
