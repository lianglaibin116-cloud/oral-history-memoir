#!/usr/bin/env python3
"""Audit detectable structure and release risks in an oral-history memoir project."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


PHASE_DIRS = {
    "setup": ["00-consent"],
    "transcription": ["00-consent", "01-audio-original", "02-asr-original", "03-transcript-edited"],
    "draft": ["00-consent", "01-audio-original", "02-asr-original", "03-transcript-edited", "04-evidence-cards", "05-drafts"],
    "final": [
        "00-consent", "01-audio-original", "02-asr-original", "03-transcript-edited",
        "04-evidence-cards", "05-drafts", "06-qa", "07-production", "08-delivery-archive",
    ],
}

UNRESOLVED = re.compile(r"(?i)\bTODO\b|\bTBD\b|待确认|转写存疑|占位|TOC_[A-Z0-9_]+|\[听不清[^\]]*\]")
RAW_SPEAKER = re.compile(r"(?i)\b(?:speaker|spk)[ _-]?\d+\b")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def add(items: list[dict[str, str]], severity: str, code: str, message: str) -> None:
    items.append({"severity": severity, "code": code, "message": message})


def has_files(path: Path, suffixes: set[str] | None = None) -> bool:
    return path.is_dir() and any(
        item.is_file() and item.stat().st_size > 0
        and (suffixes is None or item.suffix.lower() in suffixes)
        for item in path.rglob("*") if not item.name.startswith(".")
    )


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        data = archive.read("word/document.xml")
    root = ElementTree.fromstring(data)
    chunks: list[str] = []
    for node in root.iter():
        if node.tag.endswith("}t") and node.text:
            chunks.append(node.text)
        elif node.tag.endswith("}p"):
            chunks.append("\n")
    return "".join(chunks)


def extract_text(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        return extract_docx(path)
    return None


def audit_fact_ledger(root: Path, phase: str, findings: list[dict[str, str]]) -> None:
    ledger = root / "04-evidence-cards" / "fact-ledger.csv"
    if phase in {"draft", "final"} and not ledger.is_file():
        add(findings, "error", "missing_fact_ledger", f"Missing fact ledger: {ledger}")
        return
    if not ledger.is_file():
        return
    with ledger.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"fact_id", "statement", "source_file", "timecode_or_locator", "status", "allowed_use"}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            add(findings, "error", "fact_ledger_columns", "Fact ledger missing columns: " + ", ".join(missing))
            return
        unresolved_rows = []
        source_gaps = []
        count = 0
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values() if isinstance(value, str)):
                continue
            count += 1
            status = (row.get("status") or "").strip().lower()
            use = (row.get("allowed_use") or "").strip().lower()
            if status not in {"confirmed", "pending", "conflicting", "inaudible", "rejected"}:
                add(findings, "error", "invalid_fact_status", f"Invalid fact status on row {row_number}")
            if use not in {"body", "background_only", "anonymize", "do_not_use"}:
                add(findings, "error", "invalid_fact_use", f"Invalid allowed_use on row {row_number}")
            if status in {"pending", "conflicting", "inaudible", ""} and use != "do_not_use":
                unresolved_rows.append(str(row_number))
            if status == "confirmed" and not ((row.get("source_file") or "").strip() and (row.get("timecode_or_locator") or "").strip()):
                source_gaps.append(str(row_number))
        if count == 0 and phase in {"draft", "final"}:
            add(findings, "error", "empty_fact_ledger", "Fact ledger contains no evidence rows")
        if source_gaps:
            add(findings, "error", "confirmed_without_source", "Confirmed facts missing source/locator on rows: " + ", ".join(source_gaps[:20]))
        if unresolved_rows:
            severity = "error" if phase == "final" else "warning"
            add(findings, severity, "unresolved_facts", "Unresolved fact rows: " + ", ".join(unresolved_rows[:20]))


def audit_final(path: Path, findings: list[dict[str, str]]) -> dict[str, int | str]:
    metrics: dict[str, int | str] = {"file": str(path)}
    if not path.is_file():
        add(findings, "error", "missing_final", f"Final manuscript not found: {path}")
        return metrics
    try:
        text = extract_text(path)
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        add(findings, "error", "unreadable_final", f"Could not read final manuscript: {exc}")
        return metrics
    if text is None:
        add(findings, "error", "unsupported_text_check", f"Text checks not supported for {path.suffix}; supply .docx, .md or .txt and review PDF separately")
        return metrics
    if not text.strip():
        add(findings, "error", "empty_final", "Final manuscript contains no readable text")
    metrics["han_characters"] = len(HAN.findall(text))
    metrics["non_whitespace_characters"] = len(re.sub(r"\s+", "", text))
    markers = sorted(set(match.group(0) for match in UNRESOLVED.finditer(text)))
    if markers:
        add(findings, "error", "unresolved_markers", "Final manuscript contains unresolved markers: " + ", ".join(markers[:20]))
    speaker_labels = sorted(set(match.group(0) for match in RAW_SPEAKER.finditer(text)))
    if speaker_labels:
        add(findings, "error", "raw_speaker_labels", "Final manuscript contains automatic speaker labels: " + ", ".join(speaker_labels[:20]))
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project root")
    parser.add_argument("--phase", choices=PHASE_DIRS, default="final")
    parser.add_argument("--final", type=Path, help="Final .docx, .md or .txt path; PDF needs separate review")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    root = args.project.expanduser().resolve()
    findings: list[dict[str, str]] = []
    metrics: dict[str, int | str] = {}
    if not root.is_dir():
        add(findings, "error", "missing_project", f"Project directory not found: {root}")
    else:
        for name in PHASE_DIRS[args.phase]:
            if not (root / name).is_dir():
                add(findings, "error", "missing_directory", f"Missing required directory for {args.phase}: {name}")
        if not (root / "project.json").is_file():
            add(findings, "warning", "missing_metadata", "Missing project.json metadata")
        if args.phase in {"transcription", "draft", "final"}:
            for directory, code in (("01-audio-original", "no_original_audio"), ("02-asr-original", "no_raw_asr")):
                if (root / directory).is_dir() and not has_files(root / directory):
                    add(findings, "error", code, f"No files found in {directory}")
            if (root / "03-transcript-edited").is_dir() and not has_files(root / "03-transcript-edited", {".txt", ".md", ".json", ".srt", ".vtt", ".docx"}):
                add(findings, "error", "no_reviewed_transcript", "No reviewed transcript files found")
        audit_fact_ledger(root, args.phase, findings)

        final_path = args.final.expanduser().resolve() if args.final else None
        if args.phase == "final" and final_path is None:
            candidates = sorted((root / "07-production").glob("*.docx")) if (root / "07-production").is_dir() else []
            candidates += sorted((root / "07-production").glob("*.pdf")) if (root / "07-production").is_dir() else []
            if len(candidates) == 1:
                final_path = candidates[0]
            elif not candidates:
                add(findings, "error", "no_final_candidate", "No DOCX/PDF found in 07-production; pass --final")
            else:
                add(findings, "error", "ambiguous_final", "Multiple final candidates found; pass --final explicitly")
        if final_path:
            metrics.update(audit_final(final_path, findings))

    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    result = {
        "project": str(root),
        "phase": args.phase,
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "findings": findings,
        "limitations": "This audit detects structural and textual risks; human review is required for truth, consent, privacy, audio accuracy, and page layout.",
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Audit {result['status'].upper()}: {errors} error(s), {warnings} warning(s)")
        for item in findings:
            print(f"[{item['severity'].upper()}] {item['code']}: {item['message']}")
        if metrics:
            print("Metrics: " + json.dumps(metrics, ensure_ascii=False))
        print("Limitations: " + result["limitations"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
