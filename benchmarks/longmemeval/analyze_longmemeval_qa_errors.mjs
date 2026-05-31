#!/usr/bin/env node
import fs from 'node:fs';

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
const outPath = arg('--out', '');
const topK = numArg('--topk', 5);
const includeCorrect = args.includes('--include-correct');
const includeAbstention = args.includes('--include-abstention');

function normalize(text) {
  return String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}
function tokens(text) {
  return normalize(text).split(' ').filter(t => t.length > 1);
}
function tokenSet(text) {
  return new Set(tokens(text));
}
function containment(needle, haystack) {
  const a = tokenSet(needle);
  const b = tokenSet(haystack);
  if (!a.size) return 0;
  let hit = 0;
  for (const t of a) if (b.has(t)) hit += 1;
  return hit / a.size;
}
function numbers(text) {
  return [...String(text || '').matchAll(/\b\d+(?:\.\d+)?\b/g)].map(m => m[0]);
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
function sameNumbers(a, b) {
  const aa = numbers(a);
  const bb = numbers(b);
  return aa.length > 0 && aa.join('|') === bb.join('|');
}
function findHypSource(item, hypothesis) {
  const hyp = normalize(hypothesis);
  if (!hyp || hyp.length < 4) return null;
  let best = null;
  for (let i = 0; i < (item.haystack_sessions || []).length; i += 1) {
    const text = sessionText(item.haystack_sessions[i]);
    const c = containment(hypothesis, text);
    if (c >= 0.6 && (!best || c > best.containment)) {
      best = { index: i, session_id: item.haystack_session_ids?.[i] ?? String(i), date: item.haystack_dates?.[i], containment: c };
    }
  }
  return best;
}
function classify(ref, hypothesis, ok, flags) {
  if (ok) return 'correct';
  if (flags.likely_false_negative) return 'likely_false_negative';
  if (!flags.answer_session_in_topk) return 'retrieval_miss';
  if (ref.question_type === 'knowledge-update') return 'state_update';
  if (ref.question_type === 'multi-session') return 'aggregation';
  if (ref.question_type === 'temporal-reasoning') return 'temporal';
  if (ref.question_type === 'single-session-preference') return 'preference_prompt';
  if (/\b(current|currently|now|latest|new|updated|changed|still|most recent)\b/i.test(ref.question)) return 'state_update';
  if (/\b(before|after|when|first|last|earlier|later|date|day|week|month|year|since|until)\b/i.test(ref.question)) return 'temporal';
  if (/\b(all|both|list|how many|count|total|every|each|items|projects|places|events)\b/i.test(ref.question)) return 'aggregation';
  if (/\b(prefer|preference|favorite|like|love|hate|dislike|rather|enjoy)\b/i.test(ref.question)) return 'preference_prompt';
  return 'generation';
}

const refs = new Map(JSON.parse(fs.readFileSync(refPath, 'utf8')).map(x => [x.question_id, x]));
const hyps = fs.readFileSync(hypPath, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line));
const rows = [];
const summary = { total_hypotheses: hyps.length, matched_refs: 0, correct: 0, failures: 0, by_category: {}, by_question_type: {} };

for (const hyp of hyps) {
  const ref = refs.get(hyp.question_id);
  if (!ref) continue;
  if (!includeAbstention && String(ref.question_id || '').endsWith('_abs')) continue;
  summary.matched_refs += 1;
  const got = normalize(hyp.hypothesis);
  const ans = normalize(ref.answer);
  const ok = ans.length > 0 && got.includes(ans);
  if (ok) summary.correct += 1;
  else summary.failures += 1;
  const ranked = scoreSessions(ref.question, ref.haystack_sessions || []).slice(0, topK).map(([idx]) => idx);
  const topkIds = ranked.map(i => ref.haystack_session_ids?.[i] ?? String(i));
  const answerIds = new Set(ref.answer_session_ids || []);
  const answerSessionInTopk = topkIds.some(id => answerIds.has(id));
  const hypSource = findHypSource(ref, hyp.hypothesis);
  const flags = {
    answer_substring_match: ok,
    answer_session_in_topk: answerSessionInTopk,
    high_token_overlap: containment(ref.answer, hyp.hypothesis) >= 0.85,
    same_numbers: sameNumbers(ref.answer, hyp.hypothesis),
  };
  flags.likely_false_negative = flags.high_token_overlap || flags.same_numbers || (normalize(ref.answer).includes(got) && got.length > 4);
  const category = classify(ref, hyp.hypothesis, ok, flags);
  summary.by_category[category] = (summary.by_category[category] || 0) + 1;
  const type = ref.question_type || 'unknown';
  summary.by_question_type[type] ||= { total: 0, correct: 0, failures: 0, by_category: {} };
  summary.by_question_type[type].total += 1;
  summary.by_question_type[type].correct += ok ? 1 : 0;
  summary.by_question_type[type].failures += ok ? 0 : 1;
  summary.by_question_type[type].by_category[category] = (summary.by_question_type[type].by_category[category] || 0) + 1;
  if (ok && !includeCorrect) continue;
  rows.push({
    question_id: ref.question_id,
    question_type: type,
    question: ref.question,
    gold_answer: ref.answer,
    hypothesis: hyp.hypothesis,
    eval_ok: ok,
    category,
    flags,
    retrieval: { answer_session_ids: ref.answer_session_ids || [], topk_session_ids: topkIds },
    evidence: { hyp_source_session_id: hypSource?.session_id || null, hyp_source_date: hypSource?.date || null },
  });
}

summary.accuracy = summary.matched_refs ? Number((summary.correct / summary.matched_refs).toFixed(4)) : 0;
for (const v of Object.values(summary.by_question_type)) v.accuracy = v.total ? Number((v.correct / v.total).toFixed(4)) : 0;
const output = { meta: { hyp: hypPath, ref: refPath, topk: topK, metric: 'normalized-answer-substring' }, summary, rows };
const text = JSON.stringify(output, null, 2);
if (outPath) fs.writeFileSync(outPath, text + '\n');
console.log(JSON.stringify(outPath ? { ...summary, out: outPath } : output, null, 2));
