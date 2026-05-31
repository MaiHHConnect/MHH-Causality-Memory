#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}
const dataPath = arg('--data', 'benchmarks/longmemeval/data/longmemeval_oracle.json');
const outPath = arg('--out', 'benchmarks/longmemeval/results/oracle_retrieval_results.json');
const userOnly = args.includes('--user-only');

function tokens(text) {
  return String(text || '').toLowerCase().match(/[a-z0-9_]+/g)?.filter(t => t.length > 1) || [];
}

function sessionText(session) {
  return session
    .filter(turn => !userOnly || turn.role === 'user')
    .map(turn => `${turn.role || ''}: ${turn.content || ''}`)
    .join('\n');
}

function scoreSessions(question, sessions) {
  const qTokens = tokens(question);
  const docs = sessions.map(s => tokens(sessionText(s)));
  const df = new Map();
  for (const doc of docs) {
    for (const t of new Set(doc)) df.set(t, (df.get(t) || 0) + 1);
  }
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

function reciprocalRank(rankedIds, answerIds) {
  for (let i = 0; i < rankedIds.length; i += 1) {
    if (answerIds.has(rankedIds[i])) return 1 / (i + 1);
  }
  return 0;
}

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const metrics = { 'hit@1': 0, 'hit@3': 0, 'hit@5': 0, 'hit@10': 0, mrr: 0 };
const byType = new Map();
const rows = [];
let evaluated = 0;

for (const item of data) {
  if (String(item.question_id || '').endsWith('_abs')) continue;
  const answerIds = new Set(item.answer_session_ids || []);
  if (!answerIds.size) continue;
  const ranked = scoreSessions(item.question, item.haystack_sessions || []);
  const rankedIds = ranked.map(([i]) => item.haystack_session_ids[i]);
  const rr = reciprocalRank(rankedIds, answerIds);
  evaluated += 1;
  const qtype = item.question_type || 'unknown';
  if (!byType.has(qtype)) byType.set(qtype, { n: 0, 'hit@1': 0, 'hit@3': 0, 'hit@5': 0, 'hit@10': 0, mrr: 0 });
  const b = byType.get(qtype);
  b.n += 1;
  for (const k of [1, 3, 5, 10]) {
    const hit = rankedIds.slice(0, k).some(id => answerIds.has(id)) ? 1 : 0;
    metrics[`hit@${k}`] += hit;
    b[`hit@${k}`] += hit;
  }
  metrics.mrr += rr;
  b.mrr += rr;
  rows.push({ question_id: item.question_id, question_type: qtype, answer_session_ids: [...answerIds].sort(), top10: rankedIds.slice(0, 10), rr });
}

const summary = { dataset: dataPath, cases: evaluated, skipped_abstention_or_no_answer: data.length - evaluated };
for (const [k, v] of Object.entries(metrics)) summary[k] = evaluated ? Number((v / evaluated).toFixed(4)) : 0;
summary.by_type = {};
for (const [qtype, vals] of [...byType.entries()].sort()) {
  const n = vals.n;
  summary.by_type[qtype] = { n };
  for (const k of ['hit@1', 'hit@3', 'hit@5', 'hit@10', 'mrr']) summary.by_type[qtype][k] = Number((vals[k] / n).toFixed(4));
}

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify({ summary, rows }, null, 2));
console.log(JSON.stringify(summary, null, 2));
