import os
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "gbrain"))

import gbrain


class CausalChainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "brain.db")
        self.old_db = gbrain.GBRAIN_DB
        gbrain.GBRAIN_DB = self.db_path

    def tearDown(self):
        gbrain.GBRAIN_DB = self.old_db
        self.tmp.cleanup()

    def test_split_causal_items_preserves_multiline_chain(self):
        text = "2026-05-01 A -> B\n2026-05-02 B -> C\n2026-05-02 B -> C"

        items = gbrain._split_causal_items(text)

        self.assertEqual(items, ["2026-05-01 A -> B", "2026-05-02 B -> C"])

    def test_split_causal_items_splits_same_line_dated_chain(self):
        text = "2026-05-01 A -> B；2026-05-02 B -> C。2026-05-03 C -> D"

        items = gbrain._split_causal_items(text)

        self.assertEqual(items, ["2026-05-01 A -> B", "2026-05-02 B -> C", "2026-05-03 C -> D"])

    def test_split_causal_items_does_not_split_supporting_clause(self):
        text = "2026-05-01 因为 A；同时 B 作为证据 -> C"

        items = gbrain._split_causal_items(text)

        self.assertEqual(items, ["2026-05-01 因为 A；同时 B 作为证据 -> C"])

    def test_merge_causal_text_preserves_more_than_twelve_items(self):
        old = "\n".join(f"2026-05-{i:02d} old-{i} -> result-{i}" for i in range(1, 11))
        new = "\n".join(f"2026-06-{i:02d} new-{i} -> result-{i}" for i in range(1, 8))

        merged = gbrain._merge_causal_text(new, old)

        self.assertEqual(len(merged.splitlines()), 17)
        self.assertEqual(merged.splitlines()[0], "2026-06-01 new-1 -> result-1")
        self.assertEqual(merged.splitlines()[-1], "2026-05-10 old-10 -> result-10")

    def test_put_page_structured_merges_existing_causal_chain(self):
        first = self._structured("2026-05-01 旧原因 -> 旧结果", "2026-05-01 旧结果 -> 旧行动")
        second = self._structured("2026-06-01 新原因 -> 新结果", "2026-06-01 新结果 -> 新行动")

        with patch.object(gbrain, "compress_observation", side_effect=[first, second]), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("same-slug", "first content", title="same")
            gbrain.put_page_structured("same-slug", "second content", title="same")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT cause, effect FROM pages WHERE slug='same-slug'").fetchone()
        conn.close()

        self.assertEqual(row[0].splitlines(), ["2026-06-01 新原因 -> 新结果", "2026-05-01 旧原因 -> 旧结果"])
        self.assertEqual(row[1].splitlines(), ["2026-06-01 新结果 -> 新行动", "2026-05-01 旧结果 -> 旧行动"])

    def test_rebuild_causal_edges_creates_edge_per_chain_item(self):
        conn = gbrain.get_db()
        cur = conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, cause, effect)
            VALUES ('chain-page', 'Chain Page', 'body', ?, ?)
        """, ("2026-05-01 A -> B\n2026-05-02 B -> C", "2026-05-03 C -> D"))
        page_id = cur.lastrowid

        gbrain.rebuild_causal_edges_for_page(conn, page_id)
        rows = conn.execute("SELECT relation_type, evidence FROM causal_edges ORDER BY id").fetchall()
        conn.close()

        self.assertEqual([r[1] for r in rows], ["2026-05-01 A -> B", "2026-05-02 B -> C", "2026-05-03 C -> D"])

    def test_put_page_structured_writes_summary_struct_causal_items_from_fields(self):
        structured = self._structured("2026-05-01 原因A -> 结果B", "2026-05-02 结果B -> 行动C")

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("causal-items-page", "content", title="causal")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT summary_struct FROM pages WHERE slug='causal-items-page'").fetchone()
        conn.close()

        payload = json.loads(row[0])
        self.assertEqual(payload["causal_items"], [
            {"relation": "cause", "text": "2026-05-01 原因A -> 结果B"},
            {"relation": "effect", "text": "2026-05-02 结果B -> 行动C"},
        ])

    def test_rebuild_causal_edges_uses_summary_struct_causal_items(self):
        summary_struct = json.dumps({
            "type": "INSIGHT",
            "raw": "test",
            "causal_items": [
                {"relation": "cause", "text": "2026-05-01 struct cause -> page"},
                {"relation": "effect", "text": "2026-05-02 page -> struct effect"},
            ],
        }, ensure_ascii=False)

        conn = gbrain.get_db()
        cur = conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, summary_struct, cause, effect)
            VALUES ('struct-chain-page', 'Struct Chain Page', 'body', ?, '', '')
        """, (summary_struct,))
        page_id = cur.lastrowid

        gbrain.rebuild_causal_edges_for_page(conn, page_id)
        rows = conn.execute("SELECT relation_type, evidence FROM causal_edges ORDER BY id").fetchall()
        conn.close()

        self.assertEqual([r[0] for r in rows], ["cause", "effect"])
        self.assertEqual([r[1] for r in rows], [
            "2026-05-01 struct cause -> page",
            "2026-05-02 page -> struct effect",
        ])

    def test_normalize_causal_items_falls_back_to_cause_effect(self):
        items = gbrain._normalize_causal_items(
            {"type": "INSIGHT", "raw": "test"},
            "2026-05-01 old cause -> page",
            "2026-05-02 page -> old effect",
        )

        self.assertEqual(items, [
            {"relation": "cause", "text": "2026-05-01 old cause -> page"},
            {"relation": "effect", "text": "2026-05-02 page -> old effect"},
        ])

    def test_anchor_keeps_causal_lines_unflattened(self):
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, cause, effect)
            VALUES ('anchor-page', 'Anchor Page', 'memory body', ?, '')
        """, ("2026-05-01 A -> B\n2026-05-02 B -> C",))
        conn.commit()
        conn.close()

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("A", limit=5)

        self.assertIn("[anchor-page] 前因：2026-05-01 A -> B", anchor["anchor"]["因果链"])
        self.assertIn("[anchor-page] 前因：2026-05-02 B -> C", anchor["anchor"]["因果链"])

    def test_anchor_uses_summary_struct_causal_items(self):
        summary_struct = json.dumps({
            "type": "INSIGHT",
            "raw": "test",
            "causal_items": [
                {"relation": "cause", "text": "2026-05-01 struct A -> B"},
                {"relation": "effect", "text": "2026-05-02 struct B -> C"},
            ],
        }, ensure_ascii=False)
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, summary_struct, cause, effect)
            VALUES ('struct-anchor-page', 'Struct Anchor Page', 'memory body', ?, '', '')
        """, (summary_struct,))
        conn.commit()
        conn.close()

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("struct A", limit=5)

        self.assertIn("[struct-anchor-page] 前因：2026-05-01 struct A -> B", anchor["anchor"]["因果链"])
        self.assertIn("[struct-anchor-page] 后果：2026-05-02 struct B -> C", anchor["anchor"]["因果链"])

    def test_anchor_limits_injection_without_truncating_storage(self):
        cause = "\n".join(f"2026-05-{i:02d} A{i} -> B{i}" for i in range(1, 16))
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, cause, effect)
            VALUES ('long-anchor-page', 'Long Anchor Page', 'memory body', ?, '')
        """, (cause,))
        conn.commit()
        stored = conn.execute("SELECT cause FROM pages WHERE slug='long-anchor-page'").fetchone()[0]
        conn.close()

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("A", limit=5)

        self.assertEqual(len(stored.splitlines()), 15)
        self.assertEqual(len(anchor["anchor"]["因果链"]), 6)

    def test_i7_anchor_limits_answer_plan_below_timeline(self):
        summary = json.dumps({
            "type": "D5_LONGMEMEVAL_DREAM",
            "timeline": [f"2026-06-{i:02d} timeline state {i}" for i in range(1, 8)],
            "answer_plan": [f"plan {i}" for i in range(1, 8)],
        }, ensure_ascii=False)
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, summary_struct)
            VALUES ('budget-page', 'Budget Page', 'timeline plan body', ?)
        """, (summary,))
        conn.commit()
        conn.close()

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("timeline plan", limit=5)

        self.assertGreaterEqual(len(anchor["anchor"]["时间线"]), len(anchor["anchor"]["答案草稿"]))
        self.assertLessEqual(len(anchor["anchor"]["答案草稿"]), 3)

    def test_i7_anchor_timeline_prefers_dated_newer_chain(self):
        summary = json.dumps({
            "type": "W4_LONGMEMEVAL_WIKI",
            "timeline": ["2026-05-01 old state", "2026-06-01 new state"],
        }, ensure_ascii=False)
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, summary_struct)
            VALUES ('timeline-page', 'Timeline Page', 'state body', ?)
        """, (summary,))
        conn.commit()
        conn.close()

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("state", limit=5)

        timeline = anchor["anchor"]["时间线"]
        self.assertLess(
            next(i for i, v in enumerate(timeline) if "2026-06-01" in v),
            next(i for i, v in enumerate(timeline) if "2026-05-01" in v),
        )

    def test_trace_memory_deduplicates_and_sorts_edges(self):
        conn = gbrain.get_db()
        a = conn.execute("INSERT INTO pages (slug, title, compiled_truth) VALUES ('a', 'A', 'A body')").lastrowid
        b = conn.execute("INSERT INTO pages (slug, title, compiled_truth) VALUES ('b', 'B', 'B body')").lastrowid
        c = conn.execute("INSERT INTO pages (slug, title, compiled_truth) VALUES ('c', 'C', 'C body')").lastrowid
        conn.execute("INSERT INTO causal_edges (from_page, to_page, to_slug, confidence, evidence) VALUES (?, ?, 'b', 0.4, 'low')", (a, b))
        conn.execute("INSERT INTO causal_edges (from_page, to_page, to_slug, confidence, evidence) VALUES (?, ?, 'c', 0.9, 'high')", (a, c))
        conn.commit()
        conn.close()

        edges = gbrain.trace_memory("A", depth=2, limit=10)

        self.assertEqual([edge["evidence"] for edge in edges], ["high", "low"])
        self.assertEqual(len({edge["id"] for edge in edges}), len(edges))

    def test_anchor_prefers_field_evidence_over_trace_when_limited(self):
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, cause, effect)
            VALUES ('field-page', 'Field Page', 'body', '2026-05-01 direct A -> B', '')
        """)
        conn.commit()
        conn.close()
        trace = [{
            "from_slug": "trace-page",
            "relation_type": "cause",
            "to_slug": "other",
            "loose_to_slug": None,
            "evidence": "weak trace",
        }]

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=trace), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("direct A", limit=1)

        self.assertEqual(anchor["anchor"]["因果链"][0], "[field-page] 前因：2026-05-01 direct A -> B")

    def test_query_causal_uses_token_fallback_for_long_question(self):
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO pages (slug, title, compiled_truth, cause, effect)
            VALUES ('anchor-token-page', 'Token Page', 'body', '2026-05-01 认知锚定 -> 判断更稳', '')
        """)
        conn.commit()
        conn.close()

        rows = gbrain.query_causal("为什么后续判断需要认知锚定这个机制", limit=3)

        self.assertTrue(any(row["slug"] == "anchor-token-page" for row in rows))

    def test_trace_anchor_line_shows_cause_as_precondition_to_current(self):
        line = gbrain._trace_anchor_line({
            "from_slug": "current-page",
            "to_slug": "cause-page",
            "loose_to_slug": None,
            "relation_type": "cause",
            "evidence": "2026-05-01 cause -> current",
        })

        self.assertEqual(line, "cause-page --前因--> current-page；证据：2026-05-01 cause -> current")

    def test_structured_beliefs_supersede_previous_current_state(self):
        old = self._structured("", "")
        old["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "preferred_cafe",
            "value": "quiet cafe",
            "belief_type": "user_preference",
            "confidence": 0.7,
            "valid_from": "2026-05-01",
            "evidence": "2026-05-01 user chose a quiet cafe",
        }]
        new = self._structured("", "")
        new["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "preferred_cafe",
            "value": "lively cafe with music",
            "belief_type": "user_preference",
            "confidence": 0.85,
            "valid_from": "2026-06-01",
            "evidence": "2026-06-01 user said lively cafes help focus",
        }]

        with patch.object(gbrain, "compress_observation", side_effect=[old, new]), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("old-pref", "old", title="old")
            gbrain.put_page_structured("new-pref", "new", title="new")

        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT value, status, superseded_by FROM causal_beliefs
            WHERE subject='haoge' AND predicate='preferred_cafe'
            ORDER BY value
        """).fetchall()
        conn.close()

        by_value = {row[0]: row for row in rows}
        self.assertEqual(by_value["quiet cafe"][1], "superseded")
        self.assertIsNotNone(by_value["quiet cafe"][2])
        self.assertEqual(by_value["lively cafe with music"][1], "active")

    def test_user_belief_scope_and_confidence_prevent_bad_supersede(self):
        global_pref = self._structured("", "")
        global_pref["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "concise conclusion first",
            "belief_type": "user_style",
            "scope": "global",
            "confidence": 0.95,
            "evidence": "global instruction says 话少精准 and 结论先行",
        }]
        task_pref = self._structured("", "")
        task_pref["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "detailed explanation for current topic",
            "belief_type": "user_style",
            "scope": "current_task",
            "confidence": 0.8,
            "evidence": "user asked for explanation in this task",
        }]
        low_conflict = self._structured("", "")
        low_conflict["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "verbose by default",
            "belief_type": "user_style",
            "scope": "global",
            "confidence": 0.4,
            "evidence": "weak behavior inference",
        }]

        with patch.object(gbrain, "compress_observation", side_effect=[global_pref, task_pref, low_conflict]), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("global-style", "global", title="global")
            gbrain.put_page_structured("task-style", "task", title="task")
            gbrain.put_page_structured("weak-style", "weak", title="weak")

        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT value, scope, status, confidence FROM causal_beliefs
            WHERE subject='haoge' AND predicate='answer_style'
            ORDER BY confidence DESC
        """).fetchall()
        conn.close()

        by_value = {row[0]: row for row in rows}
        self.assertEqual(by_value["concise conclusion first"][2], "active")
        self.assertEqual(by_value["detailed explanation for current topic"][2], "active")
        self.assertEqual(by_value["verbose by default"][2], "active")
        self.assertEqual(by_value["detailed explanation for current topic"][1], "current_task")

    def test_non_user_belief_type_is_ignored(self):
        structured = self._structured("", "")
        structured["summary_struct"]["causal_beliefs"] = [{
            "subject": "weather",
            "predicate": "forecast",
            "value": "rainy",
            "belief_type": "external_fact",
            "confidence": 0.9,
        }]

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("weather-fact", "weather", title="weather")

        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM causal_beliefs").fetchone()[0]
        conn.close()

        self.assertEqual(count, 0)

    def test_belief_candidate_does_not_become_active_profile(self):
        structured = self._structured("", "")
        structured["summary_struct"]["belief_candidates"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "may prefer long explanations",
            "belief_type": "user_style",
            "confidence": 0.45,
            "evidence": "user asked for details once in this task",
            "reason": "single request is weak evidence",
        }]

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("weak-style-candidate", "content", title="candidate")

        conn = sqlite3.connect(self.db_path)
        active_count = conn.execute("SELECT COUNT(*) FROM causal_beliefs").fetchone()[0]
        candidate = conn.execute("""
            SELECT subject, predicate, value, candidate_status, evidence FROM belief_candidates
            WHERE source_slug='weak-style-candidate'
        """).fetchone()
        conn.close()

        self.assertEqual(active_count, 0)
        self.assertEqual(candidate[0], "haoge")
        self.assertEqual(candidate[3], "pending")
        self.assertIn("once", candidate[4])

    def test_anchor_outputs_pending_belief_candidate_as_weak_reminder(self):
        structured = self._structured("", "")
        structured["summary_struct"]["user_belief_candidates"] = [{
            "subject": "user",
            "predicate": "tooling preference",
            "value": "might prefer zero dependency tools",
            "belief_type": "user_preference",
            "confidence": 0.5,
            "evidence": "user approved a no-new-dependency approach once",
        }]

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("tooling-candidate", "content", title="candidate")

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("What tooling preference does the user have?", limit=5)

        self.assertTrue(any("might prefer zero dependency tools" in line for line in anchor["anchor"]["待确认意图/偏好线索"]))
        self.assertFalse(any("might prefer zero dependency tools" in line for line in anchor["anchor"]["意图/偏好线索"]))
        self.assertIn("待确认意图/偏好线索只能作为提醒，不能当作事实；必须有进一步证据或确认后才能采用。", anchor["anchor"]["判断约束"])

    def test_repeated_belief_candidate_accumulates_evidence_without_activation(self):
        first = self._structured("", "")
        first["summary_struct"]["belief_candidates"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "prefers concise answers",
            "belief_type": "user_style",
            "confidence": 0.4,
            "evidence": "少说废话",
        }]
        second = self._structured("", "")
        second["summary_struct"]["belief_candidates"] = [{
            "subject": "user",
            "predicate": "answer_style",
            "value": "prefers concise answers",
            "belief_type": "user_style",
            "confidence": 0.45,
            "evidence": "能一个字说清的不用两个字",
        }]

        with patch.object(gbrain, "compress_observation", side_effect=[first, second]), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("concise-candidate-1", "content", title="candidate")
            gbrain.put_page_structured("concise-candidate-2", "content", title="candidate")

        conn = sqlite3.connect(self.db_path)
        candidate = conn.execute("""
            SELECT candidate_status, confidence, evidence_count, evidence FROM belief_candidates
            WHERE subject='haoge' AND predicate='answer_style' AND value='prefers concise answers'
        """).fetchone()
        active_count = conn.execute("SELECT COUNT(*) FROM causal_beliefs").fetchone()[0]
        conn.close()

        self.assertEqual(candidate[0], "pending")
        self.assertGreater(candidate[1], 0.45)
        self.assertEqual(candidate[2], 2)
        self.assertIn("少说废话", candidate[3])
        self.assertIn("能一个字说清", candidate[3])
        self.assertEqual(active_count, 0)

    def test_can_reject_candidate_and_active_belief_without_deleting_history(self):
        structured = self._structured("", "")
        structured["summary_struct"]["belief_candidates"] = [{
            "subject": "user",
            "predicate": "tooling preference",
            "value": "prefers heavy frameworks",
            "belief_type": "user_preference",
            "confidence": 0.4,
            "evidence": "weak inference",
        }]
        active = self._structured("", "")
        active["summary_struct"]["causal_beliefs"] = [{
            "subject": "user",
            "predicate": "tooling preference",
            "value": "prefers heavy frameworks",
            "belief_type": "user_preference",
            "confidence": 0.8,
            "evidence": "old evidence",
        }]

        with patch.object(gbrain, "compress_observation", side_effect=[structured, active]), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("framework-candidate", "content", title="candidate")
            gbrain.put_page_structured("framework-active", "content", title="active")

        conn = sqlite3.connect(self.db_path)
        candidate_id = conn.execute("SELECT id FROM belief_candidates").fetchone()[0]
        belief_id = conn.execute("SELECT id FROM causal_beliefs").fetchone()[0]
        conn.close()

        self.assertTrue(gbrain.reject_belief_candidate(candidate_id, "user corrected it", "不是这个意思"))
        self.assertTrue(gbrain.reject_causal_belief(belief_id, "user corrected it", "不是这个意思"))

        conn = sqlite3.connect(self.db_path)
        candidate_status = conn.execute("SELECT candidate_status, rejection_reason FROM belief_candidates WHERE id=?", (candidate_id,)).fetchone()
        belief_status = conn.execute("SELECT status, contradiction FROM causal_beliefs WHERE id=?", (belief_id,)).fetchone()
        conn.close()

        self.assertEqual(candidate_status[0], "rejected")
        self.assertIn("corrected", candidate_status[1])
        self.assertEqual(belief_status[0], "rejected")
        self.assertIn("不是这个意思", belief_status[1])

    def test_non_haoge_subject_is_namespaced_to_prevent_profile_pollution(self):
        structured = self._structured("", "")
        structured["summary_struct"]["belief_candidates"] = [{
            "subject": "alice",
            "predicate": "answer_style",
            "value": "prefers verbose answers",
            "belief_type": "user_style",
            "confidence": 0.5,
            "evidence": "Alice said explain everything",
        }]

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("alice-candidate", "content", title="candidate")

        conn = sqlite3.connect(self.db_path)
        subject = conn.execute("SELECT subject FROM belief_candidates").fetchone()[0]
        conn.close()

        self.assertEqual(subject, "external:alice")

    def test_compress_observation_piggybacks_belief_candidates_in_single_call(self):
        class FakeResponse:
            def json(self):
                return {"choices": [{"message": {"content": json.dumps({
                    "decided": "记录风格偏好",
                    "learned": "用户要先结论",
                    "completed": "",
                    "next_steps": "",
                    "concepts": ["用户画像"],
                    "cause": "无",
                    "effect": "无",
                    "emotion": "无",
                    "causal_events": [{
                        "time": "2026-06-01",
                        "actor": "浩哥",
                        "event": "要求回答先给结论",
                        "cause": "减少废话",
                        "effect": "后续回答应更直接",
                        "evidence": "以后先给结论",
                    }],
                    "belief_candidates": [{
                        "subject": "haoge",
                        "predicate": "answer_style",
                        "value": "先给结论",
                        "belief_type": "user_style",
                        "scope": "global",
                        "confidence": 0.5,
                        "evidence": "以后先给结论",
                        "reason": "用户明确长期表达",
                    }],
                }, ensure_ascii=False)}}]}

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}), \
             patch.object(gbrain.requests, "post", return_value=FakeResponse()) as post:
            structured = gbrain.compress_observation("用户：以后先给结论", "INSIGHT")

        self.assertEqual(post.call_count, 1)
        candidates = structured["summary_struct"]["belief_candidates"]
        events = structured["summary_struct"]["causal_events"]
        self.assertEqual(events[0]["actor"], "浩哥")
        self.assertEqual(candidates[0]["belief_type"], "user_style")
        self.assertEqual(candidates[0]["evidence"], "以后先给结论")

    def test_anchor_outputs_current_belief_and_state_transition(self):
        structured = self._structured("", "")
        structured["summary_struct"].update({
            "causal_beliefs": [{
                "subject": "user",
                "predicate": "workout preference",
                "value": "prefers morning strength training after sleep improved",
                "belief_type": "user_preference",
                "confidence": 0.9,
                "valid_from": "2026-06-02",
                "evidence": "2026-06-02 user reported better energy after morning lifting",
            }],
            "state_transitions": [{
                "subject": "user",
                "state_key": "workout routine",
                "before_value": "evening cardio",
                "after_value": "morning strength training",
                "trigger": "sleep quality improved",
                "reason": "morning sessions no longer feel draining",
                "event_time": "2026-06-02",
                "confidence": 0.88,
            }],
        })

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("workout-change", "content", title="workout")

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("What workout does the user prefer now?", limit=5)

        self.assertTrue(any("morning strength training" in line for line in anchor["anchor"]["意图/偏好线索"]))
        self.assertTrue(any("evening cardio -> morning strength training" in line for line in anchor["anchor"]["用户状态变化"]))
        self.assertIn("意图/偏好线索只用于辅助解释，不能替代时人事因果事件链。", anchor["anchor"]["判断约束"])

    def test_causal_events_anchor_outputs_time_actor_event_cause_effect(self):
        structured = self._structured("", "")
        structured["summary_struct"]["causal_events"] = [{
            "time": "2026-06-01",
            "actor": "小明",
            "event": "提交了修复补丁",
            "cause": "线上任务失败需要恢复",
            "effect": "服务恢复并进入复盘",
            "context": "夜间告警后处理",
            "evidence": "2026-06-01 小明因线上任务失败提交修复补丁，服务恢复",
            "relation_type": "causal",
            "strength": "strong",
        }]

        with patch.object(gbrain, "compress_observation", return_value=structured), \
             patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("xiaoming-fix", "content", title="xiaoming")

        with patch.object(gbrain, "search_with_activation", return_value=[]), \
             patch.object(gbrain, "trace_memory", return_value=[]), \
             patch.object(gbrain, "_beads_snapshot", return_value={"available": False}):
            anchor = gbrain.build_cognitive_anchor("小明是谁，做过什么？", limit=5)

        event_lines = anchor["anchor"]["时人事因果"]
        self.assertTrue(any("人：小明" in line and "事：提交了修复补丁" in line for line in event_lines))
        self.assertTrue(any("因：线上任务失败需要恢复" in line and "果：服务恢复并进入复盘" in line for line in event_lines))
        self.assertIn("涉及人物是谁、想要什么、为什么这么做时，先拉取该人物的时人事因果链，再由模型判断。", anchor["anchor"]["判断约束"])

    def _structured(self, cause, effect):
        return {
            "decided": "",
            "learned": "",
            "completed": "",
            "next_steps": "",
            "concepts": [],
            "cause": cause,
            "effect": effect,
            "emotion": "无",
            "summary_struct": {"type": "INSIGHT", "raw": "test"},
        }


if __name__ == "__main__":
    unittest.main()
