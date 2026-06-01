import importlib.util
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "benchmarks" / "longmemeval" / "prepare_longmemeval_gbrain.py"
GBRAIN_PATH = ROOT / "scripts" / "gbrain" / "gbrain.py"
RUNNER_PATH = ROOT / "benchmarks" / "longmemeval" / "run_longmemeval_qa.mjs"


def load_module(path):
    spec = importlib.util.spec_from_file_location("prepare_lme", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LongMemEvalRealCausaMemTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.data_path = self.tmp_path / "sample.json"
        self.cache_dir = self.tmp_path / "cache"
        self.out_path = self.tmp_path / "out.jsonl"
        self.item = {
            "question_id": "leak-test",
            "question_type": "knowledge-update",
            "question_date": "2026-06-01",
            "question": "What is the current project state?",
            "answer": "SECRET_GOLD_ANSWER",
            "answer_session_ids": ["secret-label-only"],
            "haystack_session_ids": ["s1", "s2"],
            "haystack_dates": ["2026-05-30", "2026-05-31"],
            "haystack_sessions": [
                [{"role": "user", "content": "The project was blocked because the cache was stale."}],
                [{"role": "assistant", "content": "The project state was updated to ready after cache repair."}],
            ],
        }
        self.data_path.write_text(json.dumps([self.item], ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepare_creates_per_case_db_without_answer_leakage(self):
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))

        db_path = prepare.prepare_item(gbrain, self.item, self.cache_dir, force=True)

        self.assertTrue(db_path.exists())
        raw = db_path.read_bytes()
        self.assertNotIn(b"SECRET_GOLD_ANSWER", raw)
        self.assertNotIn(b"secret-label-only", raw)
        conn = sqlite3.connect(db_path)
        pages = conn.execute("SELECT COUNT(*) FROM pages WHERE type='longmemeval-session'").fetchone()[0]
        raw_events = conn.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
        conn.close()
        self.assertEqual(pages, 2)
        self.assertEqual(raw_events, 2)

    def test_prepare_manifest_excludes_gold_labels(self):
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))
        prepare.prepare_item(gbrain, self.item, self.cache_dir, force=True)
        manifest = {
            "data": str(self.data_path),
            "count": 1,
            "rows": [{"question_id": self.item["question_id"], "db": str(self.cache_dir / "leak-test.db")}],
        }
        manifest_text = json.dumps(manifest, ensure_ascii=False)
        self.assertNotIn("SECRET_GOLD_ANSWER", manifest_text)
        self.assertNotIn("secret-label-only", manifest_text)

    def test_special_question_id_uses_safe_db_name(self):
        item = {**self.item, "question_id": "id/with space"}
        data_path = self.tmp_path / "special.json"
        out_path = self.tmp_path / "special-out.jsonl"
        data_path.write_text(json.dumps([item], ensure_ascii=False), encoding="utf-8")
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))
        db_path = prepare.prepare_item(gbrain, item, self.cache_dir, force=True)
        self.assertEqual(db_path.name, "id-with-space.db")

        proc = subprocess.run(
            [
                "node", str(RUNNER_PATH),
                "--data", str(data_path),
                "--out", str(out_path),
                "--context-mode", "real_causamem",
                "--gbrain-cache-dir", str(self.cache_dir),
                "--provider", "mock",
                "--no-resume",
            ],
            text=True,
            capture_output=True,
            timeout=60,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_prepared_db_anchor_returns_context(self):
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))
        db_path = prepare.prepare_item(gbrain, self.item, self.cache_dir, force=True)

        proc = subprocess.run(
            ["/usr/bin/python3", str(GBRAIN_PATH), "anchor", self.item["question"], "--json"],
            env={**os.environ, "GBRAIN_DB": str(db_path)},
            text=True,
            capture_output=True,
            timeout=30,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        anchor = json.loads(proc.stdout)
        self.assertTrue(anchor["anchor"]["事实"] or anchor["anchor"]["因果链"])

    def test_prepare_full8_creates_layer_pages_and_anchor_sections(self):
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))

        db_path = prepare.prepare_item_full8(gbrain, self.item, self.cache_dir, force=True)

        raw = db_path.read_bytes()
        self.assertNotIn(b"SECRET_GOLD_ANSWER", raw)
        self.assertNotIn(b"secret-label-only", raw)
        conn = sqlite3.connect(db_path)
        page_types = {row[0] for row in conn.execute("SELECT DISTINCT type FROM pages").fetchall()}
        raw_events = conn.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
        candidates = conn.execute("SELECT COUNT(*) FROM memory_candidates").fetchone()[0]
        conn.close()
        self.assertIn("longmemeval-s2", page_types)
        self.assertIn("longmemeval-w4", page_types)
        self.assertIn("longmemeval-d5", page_types)
        self.assertGreaterEqual(raw_events, 2)
        self.assertGreater(candidates, 0)

        proc = subprocess.run(
            ["/usr/bin/python3", str(GBRAIN_PATH), "anchor", self.item["question"], "--json"],
            env={**os.environ, "GBRAIN_DB": str(db_path)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        anchor = json.loads(proc.stdout)["anchor"]
        self.assertTrue(anchor["直接证据"] or anchor["聚合候选"] or anchor["时间线"])

    def test_full8_answer_plan_counts_doctors_without_gold(self):
        item = {
            **self.item,
            "question_id": "doctor-plan",
            "question_type": "multi-session",
            "question": "How many different doctors did I visit?",
            "answer": "SECRET_DOCTOR_COUNT",
            "answer_session_ids": ["secret-doctor-label"],
            "haystack_session_ids": ["a", "b", "c"],
            "haystack_dates": ["2023/05/20", "2023/05/21", "2023/05/22"],
            "haystack_sessions": [
                [{"role": "user", "content": "I recently had a UTI and was prescribed antibiotics by my primary care physician, Dr. Smith."}],
                [{"role": "user", "content": "I just got diagnosed with chronic sinusitis by an ENT specialist, Dr. Patel."}],
                [{"role": "user", "content": "I got back from a follow-up appointment with my dermatologist, Dr. Lee, for a biopsy."}],
            ],
        }
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))
        db_path = prepare.prepare_item_full8(gbrain, item, self.cache_dir, force=True)

        raw = db_path.read_bytes()
        self.assertNotIn(b"SECRET_DOCTOR_COUNT", raw)
        self.assertNotIn(b"secret-doctor-label", raw)
        proc = subprocess.run(
            ["/usr/bin/python3", str(GBRAIN_PATH), "anchor", item["question"], "--json"],
            env={**os.environ, "GBRAIN_DB": str(db_path)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        anchor = json.loads(proc.stdout)["anchor"]
        joined = "\n".join(anchor["答案草稿"] + anchor["建议答案"])
        self.assertIn("Dr. Smith", joined)
        self.assertIn("Dr. Patel", joined)
        self.assertIn("Dr. Lee", joined)
        self.assertIn("3 different doctors", joined)

    def test_runner_real_mode_uses_cache_dir(self):
        prepare = load_module(PREPARE_PATH)
        gbrain = prepare.load_gbrain(str(GBRAIN_PATH))
        prepare.prepare_item(gbrain, self.item, self.cache_dir, force=True)

        proc = subprocess.run(
            [
                "node", str(RUNNER_PATH),
                "--data", str(self.data_path),
                "--out", str(self.out_path),
                "--context-mode", "bm25+real_causamem",
                "--gbrain-cache-dir", str(self.cache_dir),
                "--provider", "mock",
                "--no-resume",
            ],
            text=True,
            capture_output=True,
            timeout=60,
            cwd=str(ROOT),
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(line) for line in self.out_path.read_text().splitlines() if line.strip()]
        self.assertEqual(rows[0]["context_mode"], "bm25+real_causamem")

    def test_runner_real_mode_missing_db_fails(self):
        proc = subprocess.run(
            [
                "node", str(RUNNER_PATH),
                "--data", str(self.data_path),
                "--out", str(self.out_path),
                "--context-mode", "real_causamem",
                "--gbrain-cache-dir", str(self.cache_dir),
                "--provider", "mock",
                "--no-resume",
            ],
            text=True,
            capture_output=True,
            timeout=60,
            cwd=str(ROOT),
        )

        self.assertIn("missing per-case gbrain DB", proc.stderr)


if __name__ == "__main__":
    unittest.main()
