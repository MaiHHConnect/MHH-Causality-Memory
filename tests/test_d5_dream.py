import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "gbrain"))

import dream
import gbrain


class D5DreamTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "brain.db")
        self.memory_dir = os.path.join(self.tmp.name, "memory")
        self.wiki_dir = os.path.join(self.tmp.name, "wiki")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.old_db = gbrain.GBRAIN_DB
        self.old_memory = dream.MEMORY_DIR
        self.old_wiki = dream.WIKI_DIR
        gbrain.GBRAIN_DB = self.db_path
        dream.MEMORY_DIR = self.memory_dir
        dream.WIKI_DIR = self.wiki_dir

    def tearDown(self):
        gbrain.GBRAIN_DB = self.old_db
        dream.MEMORY_DIR = self.old_memory
        dream.WIKI_DIR = self.old_wiki
        self.tmp.cleanup()

    def test_extract_section_lines_parses_causal_chains(self):
        summary = """### 因果串线：
1. 2026-05-30 A -> B -> C
* 2026-05-31 D -> E

## 对未来的暗示
- 下一步验证 B
"""

        lines = dream.extract_section_lines(summary, "因果串线")

        self.assertEqual(lines, ["2026-05-30 A -> B -> C", "2026-05-31 D -> E"])

    def test_build_dream_structured_maps_cause_and_effect(self):
        summary = """## 关系发现
- 浩哥 和 Agent：协同增强

## 阶段判断
- CausaMem：当前阶段：证据闭环

## 因果串线
- 2026-05-30 A -> B -> C

## 对未来的暗示
- 下一步补 R0 provenance
"""

        structured = dream.build_dream_structured(summary, "2026-06-01", ["2026-05-30"])

        self.assertEqual(structured["summary_struct"]["type"], "D5_DREAM")
        self.assertEqual(structured["cause"], "2026-05-30 A -> B -> C")
        self.assertEqual(structured["effect"], "下一步补 R0 provenance")

    def test_run_big_dream_writes_deterministic_cause_to_gbrain(self):
        date = "2026-05-31"
        with open(os.path.join(self.memory_dir, f"{date}.md"), "w") as fh:
            fh.write("# 记忆\n2026-05-31 A 导致 B")
        summary = """## 因果串线
- 2026-05-31 A -> B -> C

## 对未来的暗示
- 2026-06-01 验证 C
"""

        class FixedDatetime(datetime):
            @classmethod
            def now(cls):
                return cls(2026, 6, 1)

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}), \
             patch.object(dream, "datetime", FixedDatetime), \
             patch.object(dream, "generate_dream_summary", return_value=summary), \
             patch.object(gbrain, "_embed_page_async"):
            dream.run_big_dream()

        conn = gbrain.get_db()
        row = conn.execute("SELECT type, summary_struct, cause, effect FROM pages WHERE slug='dream-2026-06-01'").fetchone()
        edges = conn.execute("SELECT evidence FROM causal_edges").fetchall()
        conn.close()

        self.assertEqual(row["type"], "dream")
        self.assertEqual(json.loads(row["summary_struct"])["type"], "D5_DREAM")
        self.assertIn("2026-05-31 A -> B -> C", row["cause"])
        self.assertIn("2026-06-01 验证 C", row["effect"])
        self.assertTrue(any("2026-05-31 A -> B -> C" in edge["evidence"] for edge in edges))

    def test_structured_override_replaces_old_dream_causal_chain(self):
        first = dream.build_dream_structured("## 因果串线\n- 2026-05-31 old -> stale\n", "2026-06-01", ["2026-05-31"])
        second = dream.build_dream_structured("## 因果串线\n- 2026-06-01 fresh -> valid\n", "2026-06-01", ["2026-06-01"])

        with patch.object(gbrain, "_embed_page_async"):
            gbrain.put_page_structured("dream-test", "first", page_type="dream", structured_override=first, merge_causal=False)
            gbrain.put_page_structured("dream-test", "second", page_type="dream", structured_override=second, merge_causal=False)

        conn = gbrain.get_db()
        row = conn.execute("SELECT cause FROM pages WHERE slug='dream-test'").fetchone()
        conn.close()

        self.assertEqual(row["cause"], "2026-06-01 fresh -> valid")


if __name__ == "__main__":
    unittest.main()
