import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "gbrain"))

import gbrain
import refine_sessions


class S2RefineSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "brain.db")
        self.old_db = gbrain.GBRAIN_DB
        gbrain.GBRAIN_DB = self.db_path

    def tearDown(self):
        gbrain.GBRAIN_DB = self.old_db
        self.tmp.cleanup()

    def test_parse_line_preserves_r0_reference(self):
        line = json.dumps({
            "timestamp": "2026-06-01T10:00:00",
            "message": {"role": "user", "content": "因为 CausaMem 报错，所以需要修复证据链。"},
        }, ensure_ascii=False)

        event = refine_sessions.parse_line(line, source_path="/tmp/session.jsonl", line_no=3)

        self.assertEqual(event["source_path"], "/tmp/session.jsonl")
        self.assertEqual(event["line_no"], 3)
        self.assertEqual(len(event["event_hash"]), 12)
        self.assertEqual(event["day"], "2026-06-01")

    def test_build_body_contains_r0_refs(self):
        items = [self._item("因为 A 导致 B")]

        body = refine_sessions.build_body("agent1", "memory-system", "2026-06-01", items)

        self.assertIn("## R0 refs", body)
        self.assertIn("/tmp/session.jsonl:1", body)
        self.assertIn("sha1=abc123", body)

    def test_structured_summary_writes_cause_effect_edges(self):
        items = [
            self._item("因为 CausaMem 缺少 R0 provenance，所以需要补证据链。"),
            self._item("完成 R0/F1 provenance 修复，下一步验证 S2。"),
        ]
        body = refine_sessions.build_body("agent1", "memory-system", "2026-06-01", items)
        structured = refine_sessions.build_structured_summary("agent1", "memory-system", "2026-06-01", items)

        with patch.object(gbrain, "_embed_page_async"):
            ok = refine_sessions.safe_put(gbrain, "refined-test", body, retries=1, structured=structured, title="agent1 memory-system")

        conn = gbrain.get_db()
        row = conn.execute("SELECT type, summary_struct, cause, effect FROM pages WHERE slug='refined-test'").fetchone()
        edges = conn.execute("SELECT evidence FROM causal_edges ORDER BY id").fetchall()
        conn.close()

        self.assertTrue(ok)
        self.assertEqual(row["type"], "refined-c1")
        summary = json.loads(row["summary_struct"])
        self.assertEqual(summary["type"], "S2_REFINED_SESSION")
        self.assertEqual(summary["r0_refs"][0]["path"], "/tmp/session.jsonl")
        self.assertIn("缺少 R0 provenance", row["cause"])
        self.assertIn("下一步验证 S2", row["effect"])
        self.assertGreaterEqual(len(edges), 2)

    def test_structured_refine_replaces_old_causal_chain(self):
        first = refine_sessions.build_structured_summary("agent1", "memory-system", "2026-06-01", [self._item("因为 old 导致 stale")])
        second = refine_sessions.build_structured_summary("agent1", "memory-system", "2026-06-01", [self._item("因为 fresh 导致 valid")])

        with patch.object(gbrain, "_embed_page_async"):
            refine_sessions.safe_put(gbrain, "refined-replace", "first", retries=1, structured=first, title="first")
            refine_sessions.safe_put(gbrain, "refined-replace", "second", retries=1, structured=second, title="second")

        conn = gbrain.get_db()
        row = conn.execute("SELECT cause FROM pages WHERE slug='refined-replace'").fetchone()
        conn.close()

        self.assertIn("fresh", row["cause"])
        self.assertNotIn("old", row["cause"])

    def _item(self, text):
        return {
            "timestamp": "2026-06-01T10:00:00",
            "day": "2026-06-01",
            "role": "user",
            "text": text,
            "source_path": "/tmp/session.jsonl",
            "line_no": 1,
            "event_hash": "abc123",
        }


if __name__ == "__main__":
    unittest.main()
