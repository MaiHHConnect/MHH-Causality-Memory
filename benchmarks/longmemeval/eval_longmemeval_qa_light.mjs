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
  return String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
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
  const ok = ans.length > 0 && got.includes(ans);
  total += 1;
  correct += ok ? 1 : 0;
  const t = ref.question_type || 'unknown';
  if (!byType.has(t)) byType.set(t, { total: 0, correct: 0 });
  byType.get(t).total += 1;
  byType.get(t).correct += ok ? 1 : 0;
}

const summary = { metric: 'normalized-answer-substring', total, correct, accuracy: total ? Number((correct / total).toFixed(4)) : 0, by_type: {} };
for (const [t, v] of [...byType.entries()].sort()) {
  summary.by_type[t] = { total: v.total, correct: v.correct, accuracy: Number((v.correct / v.total).toFixed(4)) };
}
console.log(JSON.stringify(summary, null, 2));
