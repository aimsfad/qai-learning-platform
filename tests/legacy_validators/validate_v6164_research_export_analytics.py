"""Validation for V6.16.4 research export and analytics polish."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

import research_export_center as export_center

ROOT = Path(__file__).resolve().parent
main_app = (ROOT / "main_app.py").read_text(encoding="utf-8")
db_source = (ROOT / "db.py").read_text(encoding="utf-8")
teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

static_checks = {
    "export module imported": "import research_export_center as research_export" in main_app,
    "weekly activity control": "v6164_activity_granularity" in main_app and 'to_period("W-MON")' in main_app,
    "bar activity control": "v6164_activity_chart_style" in main_app and "px.bar(activity_long" in main_app,
    "strict research export": "include_free_text=False" in main_app and "strict=True" in main_app,
    "reproducibility bundle": "build_reproducibility_bundle" in main_app,
    "specialized csv": "v6164_csv_dataset" in main_app,
    "admin confirmation gate": "v6164_confirm_admin_backup" in main_app,
    "export audit log": "export_audit_df" in db_source and "anonymized_export_prepared" in main_app,
    "strict free-text removal": "open_feedback_json" in db_source and "event_detail" in db_source,
    "production status cards": "v6164-prod-card" in teacher and "v6164-status-badge" in css,
}
failed = [name for name, ok in static_checks.items() if not ok]
if failed:
    raise AssertionError("Static checks failed: " + ", ".join(failed))

progress = pd.DataFrame(
    [
        {"participant_code": "P1", "full_name": "Name One", "study_group": "experimental", "academic_level": "Master", "is_complete_case": True, "pre_score": 40, "post_score": 70, "created_at": "2026-07-01T10:00:00Z"},
        {"participant_code": "P2", "full_name": "Name Two", "study_group": "control", "academic_level": "Licence", "is_complete_case": False, "pre_score": 55, "post_score": 60, "created_at": "2026-07-05T10:00:00Z"},
    ]
)
ai = pd.DataFrame(
    [
        {"participant_code": "P1", "prompt": "My name is One", "response": "Hello One", "mode": "llm", "created_at": "2026-07-02T10:00:00Z"},
        {"participant_code": "P2", "prompt": "question", "response": "answer", "mode": "llm", "created_at": "2026-07-06T10:00:00Z"},
    ]
)
tables = export_center.add_derived_analysis_tables({"progress_summary": progress, "ai_interactions": ai})
filters = export_center.ExportFilters(study_groups=("experimental",), completion="complete", date_from="2026-07-01", date_to="2026-07-03")
filtered = export_center.filter_export_tables(tables, filters)
assert filtered["progress_summary"]["participant_code"].tolist() == ["P1"]
assert filtered["ai_interactions"]["participant_code"].tolist() == ["P1"]
assert "paired_scores" in tables and "paper_summary" in tables

workbook = export_center.tables_to_excel_bytes(filtered, metadata={"app_version": "test"})
assert workbook[:2] == b"PK", "Excel workbook is not a valid zip-based XLSX payload"

bundle, manifest = export_center.build_reproducibility_bundle(
    filtered,
    filters=filters,
    app_version="test",
    anonymized=True,
)
assert bundle[:2] == b"PK"
with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
    names = set(archive.namelist())
    required = {
        "dataset_inventory.csv",
        "data_dictionary.csv",
        "codebook.md",
        "analysis_template.py",
        "README.txt",
        "manifest.json",
        "SHA256SUMS.txt",
        "csv/progress_summary.csv",
    }
    missing = required - names
    if missing:
        raise AssertionError(f"Bundle files missing: {sorted(missing)}")
assert manifest["filters"]["study_groups"] == ("experimental",) or manifest["filters"]["study_groups"] == ["experimental"]

inventory = export_center.dataset_inventory(filtered)
dictionary = export_center.data_dictionary(filtered)
assert not inventory.empty and not dictionary.empty
assert export_center.sha256_bytes(workbook) == export_center.sha256_bytes(workbook)

print("V6.16.4 research export and analytics validation passed.")
