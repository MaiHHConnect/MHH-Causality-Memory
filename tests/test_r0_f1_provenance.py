import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "gbrain"))

import gbrain


class R0F1ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "brain.db")
        self.old_db = gbrain.GBRAIN_DB
        gbrain.GBRAIN_DB = self.db_path

    def tearDown(self):
        gbrain.GBRAIN_DB = self.old_db
        self.tmp.cleanup()

    def test_capture_raw_event_preserves_source_session_metadata(self):
        event_id = gbrain.capture_raw_event(
            "因为 A 导致 B，所以需要记住。",
            role="user",
            session_id="s1",
            source="openclaw",
            metadata={"path": "session.jsonl", "line": 7},
        )

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT session_id, role, source, metadata, status FROM raw_events WHERE id=?", (event_id,)).fetchone()
        conn.close()

        self.assertEqual(row[0], "s1")
        self.assertEqual(row[1], "user")
        self.assertEqual(row[2], "openclaw")
        self.assertEqual(json.loads(row[3])["line"], 7)
        self.assertEqual(row[4], "raw")

    def test_extract_candidates_inherits_r0_provenance(self):
        event_id = gbrain.capture_raw_event(
            "因为 CausaMem 要承担主记忆，所以 Agent 判断前需要认知锚定。",
            role="user",
            session_id="s2",
            source="session-file",
            metadata={"path": "s2.jsonl"},
        )

        candidates = gbrain.extract_candidates()

        self.assertEqual(len(candidates), 1)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT raw_event_id, source, evidence, provenance FROM memory_candidates").fetchone()
        conn.close()
        provenance = json.loads(row[3])

        self.assertEqual(row[0], event_id)
        self.assertEqual(row[1], "session-file")
        self.assertIn("CausaMem", row[2])
        self.assertEqual(provenance["session_id"], "s2")
        self.assertEqual(provenance["metadata"]["path"], "s2.jsonl")

    def test_gate_evidence_must_match_raw_event_when_present(self):
        event_id = gbrain.capture_raw_event("真实证据：A 导致 B。", source="manual")
        conn = gbrain.get_db()
        cur = conn.execute("""
            INSERT INTO memory_candidates (raw_event_id, candidate_type, content, quality_score, source, evidence, provenance)
            VALUES (?, 'INSIGHT', '模型摘要：A 导致 B。幻觉证据：X', 0.9, 'manual', '真实证据：A 导致 B', '{}')
        """, (event_id,))
        candidate_id = cur.lastrowid
        conn.commit()
        conn.close()

        rejected = gbrain.apply_gate_decisions(json.dumps({"decisions": [{
            "candidate_id": candidate_id,
            "action": "approve",
            "confidence": 0.9,
            "evidence": "幻觉证据：X",
        }]}, ensure_ascii=False))
        approved = gbrain.apply_gate_decisions(json.dumps({"decisions": [{
            "candidate_id": candidate_id,
            "action": "approve",
            "confidence": 0.9,
            "evidence": "真实证据：A 导致 B",
        }]}, ensure_ascii=False))

        self.assertEqual(rejected[0]["gate_status"], "rejected")
        self.assertEqual(rejected[0]["reason"], "evidence_missing_or_not_in_raw_source")
        self.assertEqual(approved[0]["gate_status"], "approved")

    def test_commit_candidates_defaults_to_approved_only(self):
        conn = gbrain.get_db()
        conn.execute("""
            INSERT INTO memory_candidates (candidate_type, content, quality_score, gate_status)
            VALUES ('INSIGHT', '因为 A 导致 B，所以需要记住。', 0.9, 'ungated')
        """)
        conn.commit()
        conn.close()

        committed = gbrain.commit_candidates()

        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM pages WHERE type='memory'").fetchone()[0]
        conn.close()
        self.assertEqual(committed, [])
        self.assertEqual(count, 0)

    def test_commit_writes_page_provenance(self):
        event_id = gbrain.capture_raw_event(
            "真实证据：CausaMem 作为主记忆，所以需要判断前认知锚定。",
            role="user",
            session_id="s3",
            source="openclaw",
        )
        conn = gbrain.get_db()
        cur = conn.execute("""
            INSERT INTO memory_candidates
                (raw_event_id, candidate_type, content, quality_score, gate_status, gate_payload, source, evidence, provenance)
            VALUES (?, 'INSIGHT', 'CausaMem 作为主记忆，需要判断前认知锚定。', 0.9, 'approved', ?, 'openclaw', '真实证据：CausaMem 作为主记忆', ?)
        """, (
            event_id,
            json.dumps({"action": "approve", "confidence": 0.9, "evidence": "真实证据：CausaMem 作为主记忆"}, ensure_ascii=False),
            json.dumps({"raw_event_id": event_id, "session_id": "s3", "source": "openclaw"}, ensure_ascii=False),
        ))
        candidate_id = cur.lastrowid
        conn.commit()
        conn.close()

        with patch.object(gbrain, "_embed_page_async"):
            committed = gbrain.commit_candidates()

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT raw_event_id, candidate_id, source, session_id, evidence, provenance FROM pages WHERE id=?", (committed[0]["page_id"],)).fetchone()
        conn.close()
        provenance = json.loads(row[5])

        self.assertEqual(row[0], event_id)
        self.assertEqual(row[1], candidate_id)
        self.assertEqual(row[2], "openclaw")
        self.assertEqual(row[3], "s3")
        self.assertEqual(row[4], "真实证据：CausaMem 作为主记忆")
        self.assertEqual(provenance["candidate_id"], candidate_id)
        self.assertEqual(provenance["raw_event_id"], event_id)

    def test_import_candidates_preserves_valid_raw_event_provenance(self):
        event_id = gbrain.capture_raw_event("原始证据：A 导致 B。", session_id="s4", source="session-file")
        imported = gbrain.import_candidates(json.dumps({"candidates": [{
            "raw_event_id": event_id,
            "source": "session-file",
            "content": "A 导致 B",
            "evidence": "原始证据：A 导致 B",
            "provenance": {"path": "s4.jsonl", "line": 12},
            "score": 0.9,
        }]}, ensure_ascii=False))

        self.assertEqual(len(imported), 1)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT raw_event_id, source, evidence, provenance FROM memory_candidates").fetchone()
        conn.close()
        provenance = json.loads(row[3])

        self.assertEqual(row[0], event_id)
        self.assertEqual(row[1], "session-file")
        self.assertEqual(row[2], "原始证据：A 导致 B")
        self.assertEqual(provenance["line"], 12)
        self.assertEqual(provenance["session_id"], "s4")

    def test_existing_v4_database_gets_provenance_columns(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                type TEXT DEFAULT 'note',
                title TEXT,
                compiled_truth TEXT,
                timeline TEXT,
                summary_struct TEXT,
                concepts TEXT,
                decided TEXT,
                learned TEXT,
                completed TEXT,
                next_steps TEXT,
                cause TEXT,
                effect TEXT,
                emotion TEXT DEFAULT '无',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE memory_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_event_id INTEGER,
                candidate_type TEXT DEFAULT 'INSIGHT',
                content TEXT NOT NULL,
                cause TEXT,
                effect TEXT,
                decided TEXT,
                learned TEXT,
                next_steps TEXT,
                priority INTEGER DEFAULT 50,
                quality_score REAL DEFAULT 0.5,
                status TEXT DEFAULT 'candidate',
                committed_page INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO config (key, value) VALUES ('schema_version', '4');
        """)
        conn.close()

        conn = gbrain.get_db()
        page_cols = {row[1] for row in conn.execute("PRAGMA table_info(pages)")}
        candidate_cols = {row[1] for row in conn.execute("PRAGMA table_info(memory_candidates)")}
        version = conn.execute("SELECT value FROM config WHERE key='schema_version'").fetchone()[0]
        conn.close()

        self.assertEqual(version, str(gbrain.SCHEMA_VERSION))
        self.assertTrue({"raw_event_id", "candidate_id", "evidence", "provenance"}.issubset(page_cols))
        self.assertTrue({"source", "evidence", "provenance"}.issubset(candidate_cols))


if __name__ == "__main__":
    unittest.main()
