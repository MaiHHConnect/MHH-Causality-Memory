#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}

const basePath = arg('--base', '');
const testPath = arg('--test', '');
const refPath = arg('--ref', 'benchmarks/longmemeval/data/longmemeval_s_cleaned.json');
const outPath = arg('--out', '');
if (!basePath || !testPath) throw new Error('--base and --test are required');

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
function loadJsonl(file) {
  return new Map(fs.readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line))
    .map(row => [row.question_id, row]));
}
function isOk(ref, hyp) {
  const ans = normalize(ref?.answer);
  const got = normalize(hyp?.hypothesis);
  if (ref?.question_type === 'single-session-preference') return preferenceOverlapOk(ref.answer, hyp?.hypothesis);
  return Boolean(ans && got.includes(ans));
}
function category(baseOk, testOk) {
  if (!baseOk && testOk) return 'improved';
  if (baseOk && !testOk) return 'regressed';
  if (baseOk && testOk) return 'unchanged_correct';
  return 'unchanged_wrong';
}
function bump(obj, key) {
  obj[key] = (obj[key] || 0) + 1;
}

const refs = new Map(JSON.parse(fs.readFileSync(refPath, 'utf8')).map(row => [row.question_id, row]));
const base = loadJsonl(basePath);
const test = loadJsonl(testPath);
const rows = [];
const summary = { total: 0, improved: 0, regressed: 0, unchanged_correct: 0, unchanged_wrong: 0, base_correct: 0, test_correct: 0, by_type: {} };

for (const [questionId, ref] of refs.entries()) {
  if (!base.has(questionId) || !test.has(questionId)) continue;
  const baseRow = base.get(questionId);
  const testRow = test.get(questionId);
  const baseOk = isOk(ref, baseRow);
  const testOk = isOk(ref, testRow);
  const cat = category(baseOk, testOk);
  const type = ref.question_type || 'unknown';
  summary.total += 1;
  summary.base_correct += baseOk ? 1 : 0;
  summary.test_correct += testOk ? 1 : 0;
  bump(summary, cat);
  summary.by_type[type] ||= { total: 0, improved: 0, regressed: 0, unchanged_correct: 0, unchanged_wrong: 0, base_correct: 0, test_correct: 0 };
  summary.by_type[type].total += 1;
  summary.by_type[type].base_correct += baseOk ? 1 : 0;
  summary.by_type[type].test_correct += testOk ? 1 : 0;
  bump(summary.by_type[type], cat);
  rows.push({
    question_id: questionId,
    question_type: type,
    category: cat,
    base_ok: baseOk,
    test_ok: testOk,
    question: ref.question,
    answer: ref.answer,
    base_hypothesis: baseRow.hypothesis,
    test_hypothesis: testRow.hypothesis,
  });
}

summary.base_accuracy = summary.total ? Number((summary.base_correct / summary.total).toFixed(4)) : 0;
summary.test_accuracy = summary.total ? Number((summary.test_correct / summary.total).toFixed(4)) : 0;
summary.delta = Number((summary.test_accuracy - summary.base_accuracy).toFixed(4));
for (const v of Object.values(summary.by_type)) {
  v.base_accuracy = v.total ? Number((v.base_correct / v.total).toFixed(4)) : 0;
  v.test_accuracy = v.total ? Number((v.test_correct / v.total).toFixed(4)) : 0;
  v.delta = Number((v.test_accuracy - v.base_accuracy).toFixed(4));
}

const output = { meta: { base: basePath, test: testPath, ref: refPath, metric: 'normalized-answer-substring+preference-token-recall' }, summary, rows };
if (outPath) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(output, null, 2) + '\n');
}
console.log(JSON.stringify(outPath ? { ...summary, out: outPath } : output, null, 2));
