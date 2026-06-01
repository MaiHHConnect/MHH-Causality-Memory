#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}

const comparePath = arg('--compare', '');
const judgePath = arg('--judge', '');
const outPath = arg('--out', '');
if (!comparePath) throw new Error('--compare is required');

function loadJsonl(file) {
  if (!file || !fs.existsSync(file)) return new Map();
  return new Map(fs.readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line))
    .map(row => [row.question_id, row]));
}

const compare = JSON.parse(fs.readFileSync(comparePath, 'utf8'));
const judge = loadJsonl(judgePath);
const changed = (compare.rows || [])
  .filter(row => row.base_hypothesis !== row.test_hypothesis)
  .map(row => {
    const j = judge.get(row.question_id);
    return {
      question_id: row.question_id,
      question_type: row.question_type,
      category: row.category,
      question: row.question,
      answer: row.answer,
      base_hypothesis: row.base_hypothesis,
      test_hypothesis: row.test_hypothesis,
      judge_verdict: j?.verdict || null,
      judge_reason: j?.reason || null,
      needs_human_check: row.category === 'regressed' || !j || j.verdict !== 'correct',
    };
  });

const summary = {
  changed: changed.length,
  needs_human_check: changed.filter(row => row.needs_human_check).length,
  by_category: changed.reduce((acc, row) => ({ ...acc, [row.category]: (acc[row.category] || 0) + 1 }), {}),
};
const output = { meta: { compare: comparePath, judge: judgePath || null }, summary, changed };
if (outPath) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(output, null, 2) + '\n');
}
console.log(JSON.stringify(outPath ? { ...summary, out: outPath } : output, null, 2));
