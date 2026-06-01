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
