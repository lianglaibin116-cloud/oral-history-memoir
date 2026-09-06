"""Behavior tests with synthetic data only; no network or real interviews."""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_project
import scaffold_project


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "MEM-DEMO-001"
        scaffold_project.build_project(self.root, "MEM-DEMO-001", "合成测试", False)

    def audit(self, phase="setup", final=None):
        args = [sys.executable, "-B", str(ROOT / "scripts/audit_project.py"), str(self.root), "--phase", phase, "--json"]
        if final is not None:
            args.extend(["--final", str(final)])
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        return result.returncode, json.loads(result.stdout)

    def ledger(self, status="confirmed", source="session.wav", use="body"):
        path = self.root / "04-evidence-cards/fact-ledger.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerow(dict(fact_id="F-001", statement="合成陈述", source_file=source,
                                 timecode_or_locator="00:00:01-00:00:02", status=status, allowed_use=use))

    def test_setup_and_refuse_overwrite(self):
        self.assertEqual(self.audit()[0], 0)
        path = self.root / "project.json"
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            scaffold_project.build_project(self.root, "MEM-DEMO-001", "替换", False)
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_project_id_does_not_create_directory(self):
        target = Path(self.temp.name) / "invalid"
        with self.assertRaises(ValueError):
            scaffold_project.build_project(target, "../escape", "合成测试", False)
        self.assertFalse(target.exists())

    def test_speaker_map_is_not_a_transcript(self):
        _, report = self.audit("transcription")
        self.assertIn("no_reviewed_transcript", {f["code"] for f in report["findings"]})

    def test_empty_ledger_blocks_draft(self):
        findings = []
        audit_project.audit_fact_ledger(self.root, "draft", findings)
        self.assertIn("empty_fact_ledger", {f["code"] for f in findings})

    def test_confirmed_fact_requires_source(self):
        self.ledger(source="")
        findings = []
        audit_project.audit_fact_ledger(self.root, "final", findings)
        self.assertIn("confirmed_without_source", {f["code"] for f in findings})

    def test_unknown_status_is_not_confirmed(self):
        self.ledger(status="confrimed")
        findings = []
        audit_project.audit_fact_ledger(self.root, "final", findings)
        self.assertIn("invalid_fact_status", {f["code"] for f in findings})

    def test_excluded_pending_fact_can_remain_in_internal_ledger(self):
        self.ledger(status="pending", use="do_not_use")
        findings = []
        audit_project.audit_fact_ledger(self.root, "final", findings)
        self.assertEqual(findings, [])

    def test_split_docx_runs_are_checked(self):
        path = self.root / "07-production/test.docx"
        xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>待</w:t></w:r><w:r><w:t>确认</w:t></w:r><w:r><w:t> Speaker 0</w:t></w:r></w:p></w:body></w:document>'
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        findings = []
        metrics = audit_project.audit_final(path, findings)
        self.assertEqual(metrics["han_characters"], 3)
        self.assertEqual({f["code"] for f in findings}, {"unresolved_markers", "raw_speaker_labels"})

    def test_empty_or_unsupported_manuscript_fails(self):
        for filename, content, code in [("empty.txt", "", "empty_final"), ("example.pdf", "%PDF", "unsupported_text_check")]:
            with self.subTest(filename=filename):
                path = self.root / "07-production" / filename
                path.write_text(content, encoding="utf-8")
                findings = []
                audit_project.audit_final(path, findings)
                self.assertIn(code, {f["code"] for f in findings if f["severity"] == "error"})

    def test_missing_project_returns_json_error(self):
        self.root = Path(self.temp.name) / "missing"
        code, report = self.audit()
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "fail")


if __name__ == "__main__":
    unittest.main()
