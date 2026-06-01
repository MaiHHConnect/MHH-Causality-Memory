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
const baseJudgePath = arg('--base-judge', '');
const testJudgePath = arg('--test-judge', '');
const outPath = arg('--out', '');
const format = arg('--format', 'json');
const promptVersion = arg('--prompt-version', '');
if (!comparePath) throw new Error('--compare is required');
if (!['json', 'markdown'].includes(format)) throw new Error('--format must be json or markdown');

function loadJsonl(file) {
  if (!file || !fs.existsSync(file)) return new Map();
  return new Map(fs.readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line))
    .map(row => [row.question_id, row]));
}

function escapeMd(value) {
  return String(value ?? '').replace(/\|/g, '\\|').replace(/\n/g, '<br>');
}

function judgeSummary(row) {
  if (!row) return { verdict: null, reason: null, model: null, prompt_version: null };
  return {
    verdict: row.verdict || null,
    reason: row.reason || null,
    model: row.judge_model || row.model || null,
    prompt_version: row.prompt_version || null,
  };
}

function renderMarkdown(output) {
  const lines = [];
  lines.push('# Changed LongMemEval Cases');
  lines.push('');
  lines.push('## Meta');
  lines.push('');
  lines.push(`- compare: \`${output.meta.compare}\``);
  lines.push(`- base_judge: ${output.meta.base_judge ? `\`${output.meta.base_judge}\`` : 'null'}`);
  lines.push(`- test_judge: ${output.meta.test_judge ? `\`${output.meta.test_judge}\`` : 'null'}`);
  if (output.meta.prompt_version) lines.push(`- prompt_version: \`${output.meta.prompt_version}\``);
  lines.push('');
  lines.push('## Summary');
  lines.push('');
  lines.push(`- changed: ${output.summary.changed}`);
  lines.push(`- needs_human_check: ${output.summary.needs_human_check}`);
  lines.push(`- by_category: \`${JSON.stringify(output.summary.by_category)}\``);
  lines.push('');
  lines.push('## Cases');
  lines.push('');
  lines.push('| id | type | category | base judge | test judge | human check | question | answer |');
  lines.push('|---|---|---|---|---|---|---|---|');
  for (const row of output.changed) {
    lines.push(`| ${escapeMd(row.question_id)} | ${escapeMd(row.question_type)} | ${escapeMd(row.category)} | ${escapeMd(row.base_judge_verdict)} | ${escapeMd(row.test_judge_verdict)} | ${row.needs_human_check ? 'yes' : 'no'} | ${escapeMd(row.question)} | ${escapeMd(row.answer)} |`);
  }
  return `${lines.join('\n')}\n`;
}

const compare = JSON.parse(fs.readFileSync(comparePath, 'utf8'));
const baseJudge = loadJsonl(baseJudgePath);
const testJudge = loadJsonl(testJudgePath || judgePath);
const changed = (compare.rows || [])
  .filter(row => row.base_hypothesis !== row.test_hypothesis)
  .map(row => {
    const bj = judgeSummary(baseJudge.get(row.question_id));
    const tj = judgeSummary(testJudge.get(row.question_id));
    const hasAnyJudge = Boolean(bj.verdict || tj.verdict);
    return {
      question_id: row.question_id,
      question_type: row.question_type,
      category: row.category,
      question: row.question,
      answer: row.answer,
      base_hypothesis: row.base_hypothesis,
      test_hypothesis: row.test_hypothesis,
      base_judge_verdict: bj.verdict,
      base_judge_reason: bj.reason,
      base_judge_model: bj.model,
      base_judge_prompt_version: bj.prompt_version,
      test_judge_verdict: tj.verdict,
      test_judge_reason: tj.reason,
      test_judge_model: tj.model,
      test_judge_prompt_version: tj.prompt_version,
      judge_verdict: tj.verdict,
      judge_reason: tj.reason,
      needs_human_check: row.category === 'regressed' || !hasAnyJudge || (tj.verdict && tj.verdict !== 'correct'),
    };
  });

const summary = {
  changed: changed.length,
  needs_human_check: changed.filter(row => row.needs_human_check).length,
  by_category: changed.reduce((acc, row) => ({ ...acc, [row.category]: (acc[row.category] || 0) + 1 }), {}),
};
const output = {
  meta: {
    compare: comparePath,
    judge: judgePath || null,
    base_judge: baseJudgePath || null,
    test_judge: testJudgePath || judgePath || null,
    prompt_version: promptVersion || null,
  },
  summary,
  changed,
};
const rendered = format === 'markdown' ? renderMarkdown(output) : JSON.stringify(output, null, 2) + '\n';
if (outPath) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, rendered);
}
console.log(outPath ? JSON.stringify({ ...summary, out: outPath, format }, null, 2) : rendered.trim());
