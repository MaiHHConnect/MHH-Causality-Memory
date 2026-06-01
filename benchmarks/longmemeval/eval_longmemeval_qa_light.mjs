#!/usr/bin/env node
import fs from 'node:fs';

const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}

const hypPath = arg('--hyp', 'benchmarks/longmemeval/results/s_qa_top5.jsonl');
const refPath = arg('--ref', 'benchmarks/longmemeval/data/longmemeval_s_cleaned.json');

function normalize(text) {
  const numberWords = {
    zero: '0', one: '1', two: '2', three: '3', four: '4', five: '5',
    six: '6', seven: '7', eight: '8', nine: '9', ten: '10', eleven: '11', twelve: '12',
  };
  return String(text || '')
    .toLowerCase()
    .replace(/\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b/g, m => numberWords[m] || m)
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function contentTokens(text) {
  const stop = new Set('the user would prefer responses that their they might may not suggestions related and or of in on for with a an as such like take into account previous existing recent current specific general generic does can could should from about especially particularly include includes including utilize using build upon provide where some more this those into its also are have has been were will would'.split(' '));
  return [...new Set(String(text || '').toLowerCase().match(/[a-z0-9]+/g) || [])]
    .filter(t => t.length > 2 && !stop.has(t));
}

function preferenceOverlapOk(answer, hypothesis) {
  const refTokens = contentTokens(answer);
  if (!refTokens.length) return false;
  const hypTokens = new Set(contentTokens(hypothesis));
  const hits = refTokens.filter(t => hypTokens.has(t)).length;
  return hits / refTokens.length >= 0.3;
}

const refs = new Map(JSON.parse(fs.readFileSync(refPath, 'utf8')).map(x => [x.question_id, x]));
const hyps = fs.readFileSync(hypPath, 'utf8')
  .split('\n')
  .filter(Boolean)
  .map(line => JSON.parse(line));

const byType = new Map();
let correct = 0;
let total = 0;
for (const hyp of hyps) {
  const ref = refs.get(hyp.question_id);
  if (!ref) continue;
  const ans = normalize(ref.answer);
  const got = normalize(hyp.hypothesis);
  const ok = ref.question_type === 'single-session-preference'
    ? preferenceOverlapOk(ref.answer, hyp.hypothesis)
    : ans.length > 0 && got.includes(ans);
  total += 1;
  correct += ok ? 1 : 0;
  const t = ref.question_type || 'unknown';
  if (!byType.has(t)) byType.set(t, { total: 0, correct: 0 });
  byType.get(t).total += 1;
  byType.get(t).correct += ok ? 1 : 0;
}

const summary = { metric: 'normalized-answer-substring+preference-token-recall', total, correct, accuracy: total ? Number((correct / total).toFixed(4)) : 0, by_type: {} };
for (const [t, v] of [...byType.entries()].sort()) {
  summary.by_type[t] = { total: v.total, correct: v.correct, accuracy: Number((v.correct / v.total).toFixed(4)) };
}
console.log(JSON.stringify(summary, null, 2));
