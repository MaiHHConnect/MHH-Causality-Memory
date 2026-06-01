from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "scripts" / "wiki" / "templates"


class K4TemplateGovernanceTest(unittest.TestCase):
    def test_templates_include_source_refs_governance_frontmatter(self):
        for name in [
            "04_事件层_参考模板.md",
            "05_关系链层_参考模板.md",
            "06_抽象总结层_参考模板.md",
        ]:
            body = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
            self.assertIn("source_refs:", body)
            self.assertIn("governance:", body)
            self.assertIn("provenance_required: true", body)


if __name__ == "__main__":
    unittest.main()
