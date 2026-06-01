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
const sessionCharLimit = numArg('--session-char-limit', 0);
const limit = numArg('--limit', 0);
const offset = numArg('--offset', 0);
const model = arg('--model', 'minimax/MiniMax-M2.7-highspeed');
const provider = arg('--provider', 'openclaw-cli');
const apiBaseUrl = arg('--api-base-url', process.env.BUY_API_BASE_URL || process.env.OPENAI_BASE_URL || 'https://www.buy-api.com/v1');
const promptMode = arg('--prompt-mode', 'generic');
const contextMode = arg('--context-mode', 'bm25');
const gbrainScript = arg('--gbrain-script', 'scripts/gbrain/gbrain.py');
const gbrainDb = arg('--gbrain-db', process.env.GBRAIN_DB || '');
const gbrainCacheDir = arg('--gbrain-cache-dir', '');
const includeAbstention = args.includes('--include-abstention');
const resume = !args.includes('--no-resume');
const shardIndex = numArg('--shard-index', 0);
const shardCount = numArg('--shard-count', 1);
const maxAttempts = numArg('--max-attempts', 3);
const retryDelayMs = numArg('--retry-delay-ms', 1000);
const statusOnly = args.includes('--status-only');
const summaryPath = arg('--summary-out', outPath ? `${outPath}.summary.json` : '');

function tokens(text) {
  return String(text || '').toLowerCase().match(/[a-z0-9_]+/g)?.filter(t => t.length > 1) || [];
}

function safeId(value) {
  return String(value || 'unknown').replace(/[^a-zA-Z0-9_.-]+/g, '-').replace(/^-+|-+$/g, '') || 'unknown';
}

function sessionText(session) {
  return session.map(turn => `${turn.role || ''}: ${turn.content || ''}`).join('\n');
}

function truncateText(text, limit) {
  const value = String(text || '').trim();
  return limit > 0 && value.length > limit ? `${value.slice(0, limit)} ...[truncated]` : value;
}

function promptTurnText(turn) {
  const role = turn.role || '';
  const content = String(turn.content || '').trim();
  const limit = role === 'assistant' ? sessionCharLimit : 0;
  return `${role}: ${truncateText(content, limit)}`;
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
  return `- ${date}: ${compact}`;
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

function buildRealCausaMemContext(item) {
  const env = { ...process.env };
  if (gbrainCacheDir) {
    const dbPath = path.join(gbrainCacheDir, `${safeId(item.question_id)}.db`);
    if (!fs.existsSync(dbPath)) throw new Error(`missing per-case gbrain DB: ${dbPath}`);
    env.GBRAIN_DB = dbPath;
  } else if (gbrainDb) {
    env.GBRAIN_DB = gbrainDb;
  } else {
    throw new Error('real_causamem requires --gbrain-cache-dir or --gbrain-db; refusing to use default DB');
  }
  const res = spawnSync('/usr/bin/python3', [gbrainScript, 'anchor', item.question, '--json'], {
    encoding: 'utf8',
    env,
    maxBuffer: 10 * 1024 * 1024,
  });
  if (res.status !== 0) {
    throw new Error(`gbrain anchor exited ${res.status}: ${(res.stderr || res.stdout || '').slice(0, 1000)}`);
  }
  const anchor = JSON.parse(res.stdout);
  const body = anchor.anchor || anchor;
  const sections = ['事实', '规则', '历史决策', '直接证据', '聚合候选', '时间线', '答案草稿', '建议答案', '因果链', '执行状态', '判断约束']
    .map(key => {
      const values = Array.isArray(body[key]) ? body[key] : [];
      return `${key}:\n${values.length ? values.map(v => `- ${v}`).join('\n') : '- 待核实'}`;
    })
    .join('\n\n');
  const policy = [
    'I7 policy:',
    '- 直接证据, 时间线, 因果链 are authoritative memory evidence.',
    '- 答案草稿 and 建议答案 are low-priority hypotheses only.',
    '- Do not answer from 答案草稿/建议答案 unless supported by 直接证据 or 时间线.',
  ].join('\n');
  return `<real-causamem-context>\n${policy}\n\n${sections}\n</real-causamem-context>`;
}

function buildPrompt(item) {
  const ranked = scoreSessions(item.question, item.haystack_sessions || []).slice(0, topK);
  const chunks = ranked
    .map(([idx], i) => {
      const date = item.haystack_dates[idx];
      const content = (item.haystack_sessions[idx] || [])
        .map(turn => promptTurnText(turn))
        .join('\n\n');
      return `### Session ${i + 1}\nSession Date: ${date}\nSession Content:\n${content}`;
    })
    .join('\n\n');

  const abstentionHint = includeAbstention
    ? 'If the relevant history is insufficient to answer, say that the information is not available in the provided history.'
    : '';
  const taskHint = taskInstruction(item);
  if (!['bm25', 'causamem', 'bm25+causamem', 'real_causamem', 'bm25+real_causamem'].includes(contextMode)) throw new Error(`unsupported context mode: ${contextMode}`);
  const causamem = ['causamem', 'bm25+causamem'].includes(contextMode) ? buildCausaMemContext(item, ranked) : '';
  const realCausaMem = ['real_causamem', 'bm25+real_causamem'].includes(contextMode) ? buildRealCausaMemContext(item) : '';
  const history = contextMode === 'causamem'
    ? causamem
    : contextMode === 'bm25+causamem'
      ? `${causamem}\n\nHistory Chats:\n\n${chunks}`
      : contextMode === 'real_causamem'
        ? realCausaMem
        : contextMode === 'bm25+real_causamem'
          ? `${realCausaMem}\n\nHistory Chats:\n\n${chunks}`
          : `History Chats:\n\n${chunks}`;
  const causamemHint = ['real_causamem', 'bm25+real_causamem'].includes(contextMode)
    ? 'Use 直接证据, 时间线, and 因果链 as primary evidence. Treat 答案草稿 and 建议答案 only as low-priority hypotheses; ignore them if not directly supported by evidence.'
    : '';
  return `Question: ${item.question}\nCurrent Date: ${item.question_date}\nQuestion Type: ${item.question_type || 'unknown'}\n\nI will give you memory context between you and a user. Please answer the question above based only on the provided memory context. Give a concise direct answer. ${abstentionHint} ${taskHint} ${causamemHint}\n\n${history}\n\nAnswer:`;
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

function callOpenAICompatible(prompt) {
  const key = process.env.BUY_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) throw new Error('missing BUY_API_KEY or OPENAI_API_KEY for openai-compatible provider');
  const url = `${apiBaseUrl.replace(/\/+$/, '')}/chat/completions`;
  const requestId = `longmemeval-${Date.now()}-${Math.random().toString(16).slice(2)}`;
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

function answerQuestion(item) {
  if (provider === 'mock') {
    buildPrompt(item);
    return item.answer || '';
  }
  if (provider === 'openclaw-cli') return callOpenClaw(buildPrompt(item));
  if (provider === 'openai-compatible') return callOpenAICompatible(buildPrompt(item));
  throw new Error(`unsupported provider: ${provider}`);
}

function sleep(ms) {
  if (ms <= 0) return;
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function loadDoneIds(file) {
  const doneIds = new Set();
  let rows = 0;
  let parse_errors = 0;
  if (!fs.existsSync(file)) return { doneIds, rows, parse_errors };
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    rows += 1;
    try {
      const row = JSON.parse(line);
      if (row.question_id) doneIds.add(row.question_id);
    } catch {
      parse_errors += 1;
    }
  }
  return { doneIds, rows, parse_errors };
}

function byTypeCounts(items) {
  const out = {};
  for (const item of items) {
    const t = item.question_type || 'unknown';
    out[t] = (out[t] || 0) + 1;
  }
  return out;
}

function answerWithRetry(item) {
  let lastErr;
  const attempts = Math.max(1, maxAttempts);
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return { hypothesis: answerQuestion(item), attempts: attempt };
    } catch (err) {
      lastErr = err;
      console.error(JSON.stringify({
        ok: false,
        question_id: item.question_id,
        attempt,
        max_attempts: attempts,
        error: String(err.message || err).slice(0, 1000),
      }));
      if (attempt < attempts) sleep(retryDelayMs);
    }
  }
  throw lastErr;
}

function writeSummary(summary) {
  if (!summaryPath) return;
  fs.mkdirSync(path.dirname(summaryPath), { recursive: true });
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2) + '\n');
}

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
if (!statusOnly) fs.mkdirSync(path.dirname(outPath), { recursive: true });

const doneInfo = resume ? loadDoneIds(outPath) : { doneIds: new Set(), rows: 0, parse_errors: 0 };
const done = doneInfo.doneIds;

const selected = data
  .filter(item => includeAbstention || !String(item.question_id || '').endsWith('_abs'))
  .filter((_item, i) => shardCount <= 1 || (i % shardCount) === shardIndex)
  .slice(offset, limit > 0 ? offset + limit : undefined);
const pending = selected.filter(item => !done.has(item.question_id));
const status = {
  data: dataPath,
  out: outPath,
  selected: selected.length,
  done: selected.length - pending.length,
  pending: pending.length,
  existing_rows: doneInfo.rows,
  parse_errors: doneInfo.parse_errors,
  by_type_selected: byTypeCounts(selected),
  by_type_pending: byTypeCounts(pending),
};
if (statusOnly) {
  console.log(JSON.stringify(status, null, 2));
  process.exit(0);
}
if (!resume) {
  fs.writeFileSync(outPath, '');
  done.clear();
}

let completed = 0;
let skipped = 0;
let failed = 0;
for (const item of selected) {
  if (done.has(item.question_id)) {
    skipped += 1;
    continue;
  }
  try {
    const { hypothesis, attempts } = answerWithRetry(item);
    fs.appendFileSync(outPath, JSON.stringify({
      question_id: item.question_id,
      hypothesis,
      question_type: item.question_type,
      model,
      provider,
      topk: topK,
      session_char_limit: sessionCharLimit,
      prompt_mode: promptMode,
      context_mode: contextMode,
      attempts,
    }) + '\n');
    completed += 1;
    console.log(JSON.stringify({ ok: true, question_id: item.question_id, completed, total: selected.length }));
  } catch (err) {
    failed += 1;
    console.error(JSON.stringify({ ok: false, question_id: item.question_id, error: String(err.message || err).slice(0, 1000) }));
  }
}
const finalSummary = {
  ...status,
  completed,
  skipped,
  failed,
  remaining: Math.max(0, pending.length - completed),
  max_attempts: maxAttempts,
  retry_delay_ms: retryDelayMs,
  summary_out: summaryPath,
};
writeSummary(finalSummary);
console.log(JSON.stringify(finalSummary, null, 2));
if (failed > 0) process.exitCode = 1;
